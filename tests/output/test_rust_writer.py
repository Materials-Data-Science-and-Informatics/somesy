from pathlib import Path

import pytest

from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.rust import Rust


@pytest.fixture
def rust(load_files, file_types):
    files = load_files([file_types.RUST])
    return files[file_types.RUST]


@pytest.fixture
def rust_file(create_files, file_types):
    folder = create_files([(file_types.RUST, "Cargo.toml")])
    return folder / Path("Cargo.toml")


def test_content_match(rust):
    # create a function to check both file formats
    assert rust.name == "test-package"
    assert rust.description == "This is a test package for demonstration purposes."
    assert rust.license == "MIT" or rust.license["text"] == "MIT"
    assert len(rust.authors) == 1


def test_sync(rust, somesy_input):
    rust.sync(somesy_input.project)
    assert rust.name == "testproject"
    assert rust.version == "1.0.0"


def test_save(tmp_path, rust):
    custom_path = tmp_path / Path("Cargo.toml")
    rust.save(custom_path)
    assert custom_path.is_file()
    custom_path.unlink()


def test_from_to_person(person):
    assert Rust._from_person(person) == f"{person.full_name} <{person.email}>"

    p = Rust._to_person(Rust._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email

    # rust also has only name format
    assert Rust._to_person(person.full_name) == None


def test_person_merge(rust_file, person):
    pj = Rust(rust_file)
    # update project file with known data
    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[person.model_copy(update=dict(author=True, publication_author=True))],
    )
    pj.sync(pm)
    pj.save()
    # ----

    # jane becomes john -> modified person
    person1b = person.model_copy(
        update={"given_names": "John", "author": True, "publication_author": True}
    )

    # different Jane Doe with different orcid -> new person
    person2 = person.model_copy(
        update={
            "orcid": "https://orcid.org/4321-0987-3231",
            "email": "i.am.jane@doe.com",
            "author": True,
            "publication_author": True,
        }
    )
    # use different order, just for some difference
    person2.set_key_order(["given_names", "orcid", "family_names", "email"])

    # listed in "arbitrary" order in somesy metadata (new person comes first)
    pm.people = [person2, person1b]  # need to assign like that to keep _key_order
    pj.sync(pm)
    pj.save()

    # existing author info preserved, order not preserved because no orcid
    person1b_rep = Rust._from_person(person1b)
    person2_rep = Rust._from_person(person2)
    assert (pj.authors[0] == person1b_rep) or (pj.authors[1] == person1b_rep)
    assert (pj.authors[0] == person2_rep) or (pj.authors[1] == person2_rep)

    # new person
    person3 = Person(
        **{
            "given_names": "Janice",
            "family_names": "Doethan",
            "email": "jane93@gmail.com",
            "author": True,
            "publication_author": True,
        }
    )
    person3_rep = Rust._from_person(person3)

    # john has a new email address
    person1c = person1b.model_copy(update={"email": "john.of.us@qualityland.com"})
    person1c_rep = Rust._from_person(person1c)

    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.publication_author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    pj.sync(pm)
    pj.save()

    assert pj.authors[0] == person1c_rep
    assert pj.authors[1] == person3_rep


def test_person_merge_no_email(rust_file, person):
    # try with a rust file that has an author with only name
    r = Rust(rust_file)
    r._data["package"]["authors"] = ["Jane Doe"]
    r.save()

    # update project file with known data
    pm = ProjectMetadata(
        name="My-awesome-project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[person.model_copy(update=dict(author=True, publication_author=True))],
    )

    r.sync(pm)
    assert r.authors[0] == Rust._from_person(person)
