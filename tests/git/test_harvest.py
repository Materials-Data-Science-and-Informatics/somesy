"""Tests for Git metadata harvesting."""

import subprocess

from somesy.git import harvest


def git(path, *args):
    return subprocess.run(
        ["git", *args], cwd=path, check=True, capture_output=True, text=True
    )


def test_harvest_returns_somesy_relevant_metadata(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Jane Doe")
    git(tmp_path, "config", "user.email", "jane@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "README.md").write_text("project")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-qm", "initial")
    git(tmp_path, "tag", "v1.2.0")
    (tmp_path / "README.md").write_text("project\nupdated")
    git(tmp_path, "commit", "-qam", "update")

    metadata = harvest(tmp_path)

    assert metadata is not None
    assert metadata.name == tmp_path.name
    assert metadata.repository is None
    assert metadata.version == "v1.2.0"
    assert metadata.authors[0].name == "Jane Doe"
    assert metadata.authors[0].email == "jane@example.com"
    assert metadata.authors[0].commit_count == 2
    assert metadata.authors[0].author is True
    assert [str(t) for t in metadata.authors[0].contribution_types] == ["code"]


def test_harvest_returns_none_outside_git_repository(tmp_path):
    assert harvest(tmp_path) is None
