import pytest

from somesy.mkdocs import MkDocs
from somesy.core.models import Person


@pytest.fixture
def mkdocs(load_files, file_types):
    files = load_files([file_types.MKDOCS])
    return files[file_types.MKDOCS]


def test_content_match(mkdocs: MkDocs):
    assert mkdocs.name == "test-package"
    assert mkdocs.description == "This is a test package for demonstration purposes."
    assert len(mkdocs.authors) == 0


def test_sync(mkdocs: MkDocs, somesy_input: dict):
    mkdocs.sync(somesy_input.project)
    assert mkdocs.name == "testproject"
    assert mkdocs.authors[0] == "John Doe <john.doe@example.com>"
    assert mkdocs.repo_name == "/example/testproject"


def test_save(tmp_path):
    # test save with default path
    file_path = tmp_path / "mkdocs.yml"
    mkdocs = MkDocs(file_path, create_if_not_exists=True)
    mkdocs.save()
    assert file_path.is_file()

    # test save with custom path
    custom_path = tmp_path / "mkdocs2.yml"
    mkdocs.save(custom_path)
    assert custom_path.is_file()


def test_from_person(person: Person):
    p = MkDocs._to_person(MkDocs._from_person(person))
    assert p.to_name_email_string() == person.to_name_email_string()
