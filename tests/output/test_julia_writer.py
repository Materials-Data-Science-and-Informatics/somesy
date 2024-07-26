from pathlib import Path

import pytest

from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.julia.writer import Julia


@pytest.fixture
def julia(load_files, file_types):
    files = load_files([file_types.JULIA])
    return files[file_types.JULIA]


@pytest.fixture
def julia_file(create_files, file_types):
    folder = create_files([(file_types.JULIA, "Project.toml")])
    return folder / Path("Project.toml")


def test_content_match(julia):
    assert julia.name == "test-package"
    assert len(julia.authors) == 1


def test_sync(julia, somesy_input):
    julia.sync(somesy_input.project)
    assert julia.name == "testproject"
    assert julia.version == "1.0.0"


def test_save(tmp_path, julia):
    custom_path = tmp_path / Path("Project.toml")
    julia.save(custom_path)
    assert custom_path.is_file()
    custom_path.unlink()


def test_from_to_person(person):
    assert Julia._from_person(person) == f"{person.full_name} <{person.email}>"

    p = Julia._to_person(Julia._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email


def test_person_merge(request, julia_file, person):
    pj = Julia(julia_file)
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
    person1b_rep = Julia._from_person(person1b)
    person2_rep = Julia._from_person(person2)
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
    person3_rep = Julia._from_person(person3)

    # john has a new email address
    person1c = person1b.model_copy(update={"email": "john.of.us@qualityland.com"})
    person1c_rep = Julia._from_person(person1c)

    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.publication_author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    pj.sync(pm)
    pj.save()

    assert len(pj.authors) == 2
    assert pj.authors[0] == person1c_rep
    assert pj.authors[1] == person3_rep


def test_without_email(tmp_path, person):
    project_toml_str = """
        name = "test-package"
        version = "0.1.0"
        authors = ["Jane Doe"]
        uuid = "608dde89-f1f1-4a1a-863e-3c5da0c9a9e3"
    """
    # save to file
    project_file = tmp_path / Path("Project.toml")
    project_file.write_text(project_toml_str)

    # load and sync
    pj = Julia(project_file)

    assert len(pj.authors) == 0

    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[
            person.model_copy(
                update=dict(author=True, publication_author=True, maintainer=True)
            )
        ],
    )

    pj.sync(pm)

    assert len(pj.authors) == 1
    assert pj.authors[0] == f"{person.full_name} <{person.email}>"
