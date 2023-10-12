from pathlib import Path
import pytest

from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.pyproject.writer import Poetry, SetupTools


@pytest.fixture
def pyproject_poetry(load_files, file_types):
    files = load_files([file_types.POETRY])
    return files[file_types.POETRY]


@pytest.fixture
def pyproject_poetry_file(create_files, file_types):
    folder = create_files([(file_types.POETRY, "pyproject.toml")])
    return folder / Path("pyproject.toml")


@pytest.fixture
def pyproject_setuptools(load_files, file_types):
    files = load_files([file_types.SETUPTOOLS])
    return files[file_types.SETUPTOOLS]


@pytest.fixture
def pyproject_setuptools_file(create_files, file_types):
    folder = create_files([(file_types.SETUPTOOLS, "pyproject.toml")])
    return folder / Path("pyproject.toml")


def test_content_match(pyproject_poetry, pyproject_setuptools):
    # create a function to check both file formats
    def assert_content_match(pyproject_file):
        assert pyproject_file.name == "test-package"
        assert (
            pyproject_file.description
            == "This is a test package for demonstration purposes."
        )
        assert pyproject_file.license == "MIT"
        assert len(pyproject_file.authors) == 1

    # assert for both formats
    assert_content_match(pyproject_poetry)
    assert_content_match(pyproject_setuptools)


def test_sync(pyproject_poetry, pyproject_setuptools, somesy_input):
    def assert_sync(pyproject):
        pyproject.sync(somesy_input.project)
        assert pyproject.name == "testproject"
        assert pyproject.version == "1.0.0"

    assert_sync(pyproject_poetry)
    assert_sync(pyproject_setuptools)


def test_save(tmp_path, pyproject_poetry, pyproject_setuptools):
    def assert_save(pyproject):
        custom_path = tmp_path / Path("pyproject.toml")
        pyproject.save(custom_path)
        assert custom_path.is_file()
        custom_path.unlink()

    assert_save(pyproject_poetry)
    assert_save(pyproject_setuptools)


def test_from_to_person(person):
    # test for poetry
    assert Poetry._from_person(person) == f"{person.full_name} <{person.email}>"

    p = Poetry._to_person(Poetry._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email

    # test for setuptools
    assert SetupTools._from_person(person) == {
        "name": person.full_name,
        "email": person.email,
    }

    p = SetupTools._to_person(SetupTools._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email


def test_person_merge_poetry(pyproject_poetry_file, person):
    pj = Poetry(pyproject_poetry_file)

    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        people=[person.copy(update=dict(author=True, publication_author=True))],
    )
    pj.sync(pm)
    pj.save()

    # jane becomes john -> modified person
    person1b = person.copy(
        update={"given_names": "John", "author": True, "publication_author": True}
    )

    # different Jane Doe with different orcid -> new person
    person2 = person.copy(
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
    person1b_str = f"{person1b.full_name} <{person1b.email}>"
    assert (pj.authors[0] == person1b_str) or (pj.authors[1] == person1b_str)

    person2_str = f"{person2.full_name} <{person2.email}>"
    assert (pj.authors[0] == person2_str) or (pj.authors[1] == person2_str)

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
    # john has a new email address
    person1c = person1b.copy(update={"email": "john.of.us@qualityland.com"})
    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.publication_author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    pj.sync(pm)
    pj.save()

    assert len(pj.maintainers) == 1
    assert pj.authors[0] == f"{person1c.full_name} <{person1c.email}>"
    assert pj.authors[1] == f"{person3.full_name} <{person3.email}>"


def test_person_merge_setuptools(pyproject_setuptools_file, person):
    pj = SetupTools(pyproject_setuptools_file)

    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        people=[person.copy(update=dict(author=True, publication_author=True))],
    )
    pj.sync(pm)
    pj.save()

    # jane becomes john -> modified person
    person1b = person.copy(
        update={"given_names": "John", "author": True, "publication_author": True}
    )

    # different Jane Doe with different orcid -> new person
    person2 = person.copy(
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
    person1b_dump = {"name": person1b.full_name, "email": person1b.email}
    assert (pj.authors[0] == person1b_dump) or (pj.authors[1] == person1b_dump)

    person2_dump = {"name": person2.full_name, "email": person2.email}
    assert (pj.authors[0] == person2_dump) or (pj.authors[1] == person2_dump)

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
    # john has a new email address
    person1c = person1b.copy(update={"email": "john.of.us@qualityland.com"})
    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.publication_author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    pj.sync(pm)
    pj.save()

    assert len(pj.maintainers) == 1
    assert pj.authors[0] == {"name": person1c.full_name, "email": person1c.email}
    assert pj.authors[1] == {"name": person3.full_name, "email": person3.email}
