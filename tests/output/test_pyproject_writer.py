from pathlib import Path
import pytest

from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.pyproject.writer import Poetry, Pyproject, PyprojectCommon, SetupTools


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


def test_person_merge_poetry(pyproject_poetry_file, person: Person):
    #TODO: package.json is a good example