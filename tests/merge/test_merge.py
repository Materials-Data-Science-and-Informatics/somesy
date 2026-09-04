"""Tests for harvested metadata merging."""

import subprocess

import pytest

from somesy.core.models import Person
from somesy.git.harvest import harvest
from somesy.git.models import GitAuthor, GitMetadata
from somesy.harvest import harvest_sources
from somesy.merge import merge_metadata


def test_merge_metadata_prefers_first_scalar_and_fills_people():
    result = merge_metadata(
        [
            {
                "name": "project",
                "description": "description",
                "license": "MIT",
                "people": [
                    Person(
                        given_names="Jane",
                        family_names="Doe",
                        author=True,
                    )
                ],
                "keywords": {"metadata"},
            },
            {
                "name": "other-name",
                "license": "Apache-2.0",
                "people": [
                    Person(
                        given_names="Jane",
                        family_names="Doe",
                        email="jane@example.com",
                        contribution_types=["code"],
                    )
                ],
                "keywords": {"software"},
            },
        ]
    )

    assert result.name == "project"
    assert str(result.license) == "MIT"
    assert result.keywords == ["metadata", "software"]
    assert len(result.people) == 1
    assert result.people[0].email == "jane@example.com"
    assert [str(value) for value in (result.people[0].contribution_types or [])] == [
        "code"
    ]


def test_merge_metadata_adds_git_authors_as_code_authors():
    result = merge_metadata(
        [{"name": "project", "description": "description", "license": "MIT"}],
        GitMetadata(
            name="git-project",
            repository="git@github.com:example/project.git",
            version="v1.0.0",
            authors=[GitAuthor(name="Jane Doe", email="jane@example.com")],
        ),
    )

    assert str(result.repository) == "https://github.com/example/project.git"
    assert result.version == "v1.0.0"
    assert result.people[0].author is True
    assert [str(value) for value in (result.people[0].contribution_types or [])] == [
        "code"
    ]


def _commit(path, name, email, message):
    subprocess.run(["git", "config", "user.name", name], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", email], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=path, check=True)


@pytest.mark.parametrize(
    "file_types_to_create",
    [
        ["pyproject"],
        ["package_json"],
        ["pom"],
        ["pyproject", "package_json"],
    ],
)
def test_merge_real_endpoint_files_and_multiple_git_authors(
    tmp_path, create_files, file_types, file_types_to_create
):
    type_map = {
        "pyproject": (file_types.POETRY, "pyproject.toml"),
        "package_json": (file_types.PACKAGE_JSON, "package.json"),
        "pom": (file_types.POM_XML, "pom.xml"),
    }
    create_files({type_map[file_type] for file_type in file_types_to_create})
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True
    )
    _commit(tmp_path, "Git One", "one@example.com", "initial")
    (tmp_path / "README.md").write_text("updated")
    _commit(tmp_path, "Git Two", "two@example.com", "update")

    result = merge_metadata(
        [metadata for _, metadata in harvest_sources(tmp_path)], harvest(tmp_path)
    )

    assert result.name == "test-package"
    assert {person.full_name for person in result.people} >= {"Git One", "Git Two"}
    git_people = {
        person.full_name: person
        for person in result.people
        if person.email in {"one@example.com", "two@example.com"}
    }
    assert all(person.author for person in git_people.values())
    assert all(
        [str(value) for value in (person.contribution_types or [])] == ["code"]
        for person in git_people.values()
    )
