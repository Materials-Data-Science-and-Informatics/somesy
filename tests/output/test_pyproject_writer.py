from pathlib import Path

import pytest

from somesy.core.models import LicenseEnum, Person, ProjectMetadata, Entity
from somesy.pyproject.writer import Poetry, SetupTools


@pytest.fixture
def pyproject_poetry(load_files, file_types):
    files = load_files([file_types.POETRY])
    return files[file_types.POETRY]


@pytest.fixture
def pyproject_poetry2(load_files, file_types):
    files = load_files([file_types.POETRY2])
    return files[file_types.POETRY2]


@pytest.fixture
def pyproject_poetry_file(create_files, file_types):
    folder = create_files([(file_types.POETRY, "pyproject.toml")])
    return folder / Path("pyproject.toml")


@pytest.fixture
def pyproject_poetry2_file(create_files, file_types):
    folder = create_files([(file_types.POETRY2, "pyproject2.toml")])
    return folder / Path("pyproject2.toml")


@pytest.fixture
def pyproject_setuptools(load_files, file_types):
    files = load_files([file_types.SETUPTOOLS])
    return files[file_types.SETUPTOOLS]


@pytest.fixture
def pyproject_setuptools_file(create_files, file_types):
    folder = create_files([(file_types.SETUPTOOLS, "pyproject.toml")])
    return folder / Path("pyproject.toml")


def test_content_match(pyproject_poetry, pyproject_poetry2, pyproject_setuptools):
    # create a function to check both file formats
    def assert_content_match(pyproject_file):
        assert pyproject_file.name == "test-package"
        assert (
            pyproject_file.description
            == "This is a test package for demonstration purposes."
        )
        license_text = pyproject_file.license
        if isinstance(license_text, dict):
            license_text = license_text["text"]
        if isinstance(license_text, str):
            assert license_text == "MIT"
        else:
            assert license_text.text.value == "MIT"
        assert len(pyproject_file.authors) == 1

    # assert for all formats
    assert_content_match(pyproject_poetry)
    assert_content_match(pyproject_poetry2)
    assert_content_match(pyproject_setuptools)


def test_sync(pyproject_poetry, pyproject_poetry2, pyproject_setuptools, somesy_input):
    def assert_sync(pyproject):
        pyproject.sync(somesy_input.project)
        assert pyproject.name == "testproject"
        assert pyproject.version == "1.0.0"

    assert_sync(pyproject_poetry)
    assert_sync(pyproject_poetry2)
    assert_sync(pyproject_setuptools)


def test_save(tmp_path, pyproject_poetry, pyproject_poetry2, pyproject_setuptools):
    def assert_save(pyproject):
        custom_path = tmp_path / Path("pyproject.toml")
        pyproject.save(custom_path)
        assert custom_path.is_file()
        custom_path.unlink()

    assert_save(pyproject_poetry)
    assert_save(pyproject_poetry2)
    assert_save(pyproject_setuptools)


def test_from_to_person(person):
    # test for poetry
    assert Poetry._from_person(person) == f"{person.full_name} <{person.email}>"

    p = Poetry._to_person(Poetry._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email

    p = Poetry._to_person("John Doe")
    assert p.given_names == "John"
    assert p.family_names == "Doe"

    e = Poetry._to_person("Entity")
    assert isinstance(e, Entity)
    assert e.name == "Entity"

    # test for setuptools
    assert SetupTools._from_person(person) == {
        "name": person.full_name,
        "email": person.email,
    }

    p = SetupTools._to_person(SetupTools._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email


@pytest.mark.parametrize(
    "writer_class, writer_file_fixture, version",
    [
        (Poetry, "pyproject_poetry_file", 1),
        (Poetry, "pyproject_poetry2_file", 2),
        (SetupTools, "pyproject_setuptools_file", None),
    ],
)
def test_person_merge_pyproject(
    request, writer_class, writer_file_fixture, version, person
):
    # get suitable project file
    writer_file = request.getfixturevalue(writer_file_fixture)

    # Initialize with correct version for Poetry
    if writer_class == Poetry:
        pj = writer_class(writer_file, version=version)
    else:
        pj = writer_class(writer_file)

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
    if version is not None:
        person1b_rep = writer_class._from_person(person1b, poetry_version=version)
        person2_rep = writer_class._from_person(person2, poetry_version=version)
    else:
        person1b_rep = writer_class._from_person(person1b)
        person2_rep = writer_class._from_person(person2)
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
    if version is not None:
        person3_rep = writer_class._from_person(person3, poetry_version=version)
    else:
        person3_rep = writer_class._from_person(person3)

    # john has a new email address
    person1c = person1b.model_copy(update={"email": "john.of.us@qualityland.com"})
    if version is not None:
        person1c_rep = writer_class._from_person(person1c, poetry_version=version)
    else:
        person1c_rep = writer_class._from_person(person1c)

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
    assert pj.authors[0] == person1c_rep
    assert pj.authors[1] == person3_rep


def test_without_email(tmp_path, person):
    # Test Poetry v1
    pyproject_v1_str = """
    [tool.poetry]
    name = "ttt"
    version = "0.1.0"
    description = "asd"
    authors = ["John Doe"]
    license = "MIT"

    [tool.poetry.dependencies]
    python = "^3.10"

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"
    """

    # Test Poetry v2
    pyproject_v2_str = """
    [tool.poetry]
    name = "ttt"
    version = "0.1.0"
    description = "asd"
    authors = ["John Doe"]
    license = "MIT"

    [project]
    name = "ttt"
    version = "0.1.0"
    description = "asd"
    authors = ["John Doe"]
    license = "MIT"

    [tool.poetry.dependencies]
    python = "^3.10"

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"
    """

    # Test both versions
    for pyproject_str, version in [(pyproject_v1_str, 1), (pyproject_v2_str, 2)]:
        # save to file
        pyproject_file = tmp_path / Path(f"pyproject_v{version}.toml")
        pyproject_file.write_text(pyproject_str)

        # load and sync
        p = Poetry(pyproject_file, version=version)
        assert len(p.authors) == 1

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

        p.sync(pm)

        assert len(p.authors) == 1
        assert len(p.maintainers) == 1
