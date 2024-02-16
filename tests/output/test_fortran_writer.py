from pathlib import Path

import pytest

from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.fortran.writer import Fortran


@pytest.fixture
def fortran(load_files, file_types):
    files = load_files([file_types.FORTRAN])
    return files[file_types.FORTRAN]


@pytest.fixture
def fortran_file(create_files, file_types):
    folder = create_files([(file_types.FORTRAN, "fpm.toml")])
    return folder / Path("fpm.toml")


def test_content_match(fortran):
    assert fortran.name == "test-package"
    assert len(fortran.authors) == 1


def test_sync(fortran, somesy_input):
    # with 'full name <email>' format
    fortran.sync(somesy_input.project)
    assert fortran.name == "testproject"
    assert fortran.version == "1.0.0"
    assert fortran.authors[0] == "John Doe <john.doe@example.com>"


def test_sync_free_text(fortran_file, somesy_input):
    # update author to have a free text format
    content = fortran_file.read_text()
    content = content.replace(
        'author = "John Doe <john.doe@example.com>"', 'author = "John Doe"'
    )

    # write the new content
    fortran_file.write_text(content)

    # read the file again
    fortran = Fortran(fortran_file)
    fortran.sync(somesy_input.project)
    assert fortran.name == "testproject"
    assert fortran.version == "1.0.0"
    assert fortran.authors[0] == "John Doe <john.doe@example.com>"


def test_save(tmp_path, fortran):
    custom_path = tmp_path / Path("fpm.toml")
    fortran.save(custom_path)
    assert custom_path.is_file()
    custom_path.unlink()


def test_from_person(person):
    assert Fortran._from_person(person) == f"{person.full_name} <{person.email}>"
