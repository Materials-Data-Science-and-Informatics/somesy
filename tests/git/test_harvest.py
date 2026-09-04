"""Tests for Git metadata harvesting."""

import os
import subprocess
from datetime import date

from somesy.git import harvest


def git(path, *args, env=None):
    return subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def test_harvest_returns_somesy_relevant_metadata(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Jane Doe")
    git(tmp_path, "config", "user.email", "jane@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "README.md").write_text("project")
    git(tmp_path, "add", "README.md")
    initial_date = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2023-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2023-01-01T00:00:00Z",
    }
    git(tmp_path, "commit", "-qm", "initial", env=initial_date)
    git(tmp_path, "tag", "v1.2.0")
    (tmp_path / "README.md").write_text("project\nupdated")
    update_date = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2024-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2024-01-01T00:00:00Z",
    }
    git(tmp_path, "commit", "-qam", "update", env=update_date)

    metadata = harvest(tmp_path)

    assert metadata is not None
    assert metadata.name == tmp_path.name
    assert metadata.repository is None
    assert metadata.version == "v1.2.0"
    assert metadata.date_created == date(2023, 1, 1)
    assert metadata.date_modified == date(2024, 1, 1)
    assert metadata.authors[0].name == "Jane Doe"
    assert metadata.authors[0].email == "jane@example.com"
    assert metadata.authors[0].commit_count == 2
    assert metadata.authors[0].author is True
    assert [str(t) for t in metadata.authors[0].contribution_types] == ["code"]


def test_harvest_returns_none_outside_git_repository(tmp_path):
    assert harvest(tmp_path) is None
