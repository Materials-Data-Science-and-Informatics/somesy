import pytest

from somesy.core.models import Person
from somesy.mkdocs import MkDocs


@pytest.fixture
def mkdocs(load_files, file_types):
    files = load_files([file_types.MKDOCS])
    return files[file_types.MKDOCS]


def test_content_match(mkdocs: MkDocs):
    assert mkdocs.name == "test-package"
    assert mkdocs.description == "This is a test package for demonstration purposes."
    assert len(mkdocs.authors) == 1


def test_sync(mkdocs: MkDocs, somesy_input: dict):
    mkdocs.sync(somesy_input.project)
    assert mkdocs.name == "testproject"
    assert mkdocs.authors[0] == "John Doe <john.doe@example.com>"
    # user-set repo_name is kept
    assert mkdocs._get_property("repo_name") == "/example/test-package"


def test_sync_writes_repo_name_if_absent(tmp_path, somesy_input):
    path = tmp_path / "mkdocs.yml"
    path.write_text("site_name: My Docs\n")
    mkdocs = MkDocs(path)
    mkdocs.sync(somesy_input.project)
    mkdocs.save()
    assert "repo_name: example/testproject\n" in path.read_text()


def test_free_text_site_name(tmp_path):
    path = tmp_path / "mkdocs.yml"
    path.write_text("site_name: My Docs\n")
    assert MkDocs(path).name == "My Docs"


def test_null_site_description(tmp_path, somesy_input):
    path = tmp_path / "mkdocs.yml"
    path.write_text("site_name: Docs\nsite_description:\n")
    mkdocs = MkDocs(path)
    mkdocs.save()
    mkdocs.sync(somesy_input.project)
    mkdocs.save()


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
    assert p is not None
    assert p.to_name_email_string() == person.to_name_email_string()
