"""Tests for Git metadata harvesting."""

import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

from somesy.git import harvest
from somesy.git.harvest import _git


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


def test_harvest_omits_creation_date_for_shallow_repository(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-q")
    git(source, "config", "user.name", "Jane Doe")
    git(source, "config", "user.email", "jane@example.com")
    git(source, "config", "commit.gpgsign", "false")
    (source / "README.md").write_text("project")
    git(source, "add", "README.md")
    git(
        source,
        "commit",
        "-qm",
        "initial",
        env={
            **os.environ,
            "GIT_AUTHOR_DATE": "2023-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2023-01-01T00:00:00Z",
        },
    )
    (source / "README.md").write_text("project\nupdated")
    git(source, "add", "README.md")
    git(
        source,
        "commit",
        "-qm",
        "update",
        env={
            **os.environ,
            "GIT_AUTHOR_DATE": "2024-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2024-01-01T00:00:00Z",
        },
    )
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--depth=1", f"file://{source}", str(clone)], check=True
    )

    metadata = harvest(clone)

    assert metadata is not None
    assert metadata.date_created is None
    assert metadata.date_modified == date(2024, 1, 1)


def _init_repo(path):
    git(path, "init", "-q")
    git(path, "config", "user.name", "Jane Doe")
    git(path, "config", "user.email", "jane@example.com")
    git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("project")
    git(path, "add", "README.md")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://oauth2:SECRET@gitlab.example.org/a/b.git",
            "https://gitlab.example.org/a/b.git",
        ),
        (
            "https://SECRET@gitlab.example.org:8443/a/b.git",
            "https://gitlab.example.org:8443/a/b.git",
        ),
        ("https://gitlab.example.org/a/b.git", "https://gitlab.example.org/a/b.git"),
        ("git@gitlab.example.org:a/b.git", "git@gitlab.example.org:a/b.git"),
    ],
)
def test_harvest_strips_remote_credentials(tmp_path, url, expected):
    _init_repo(tmp_path)
    git(tmp_path, "commit", "-qm", "initial")
    git(tmp_path, "remote", "add", "origin", url)

    metadata = harvest(tmp_path)

    assert metadata is not None
    assert metadata.repository == expected


def test_harvest_without_git_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)

    assert harvest(tmp_path) is None


@pytest.mark.skipif(
    not hasattr(os, "environb"), reason="needs bytes environment (POSIX only)"
)
def test_harvest_tolerates_non_utf8_author(tmp_path):
    _init_repo(tmp_path)
    envb = {**os.environb, b"GIT_AUTHOR_NAME": "Jos\xe9".encode("latin-1")}
    envb[b"GIT_AUTHOR_EMAIL"] = b"jose@example.com"
    subprocess.run(
        ["git", "commit", "-qm", "initial"],
        cwd=tmp_path,
        check=True,
        env=envb,
    )

    metadata = harvest(tmp_path)

    assert metadata is not None
    assert [a.name[:3] for a in metadata.authors] == ["Jos"]


def test_git_decodes_invalid_utf8_with_replacement(tmp_path, monkeypatch):
    # Git may emit raw non-UTF-8 bytes; they must not raise UnicodeDecodeError.
    real_run = subprocess.run
    code = "import sys; sys.stdout.buffer.write(b'Jos\\xe9')"

    def fake_run(cmd, **kwargs):
        return real_run([sys.executable, "-c", code], **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _git(tmp_path, "log") == "Jos\ufffd"


def test_harvest_defaults_to_current_directory(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    git(tmp_path, "commit", "-qm", "initial")
    monkeypatch.chdir(tmp_path)

    metadata = harvest()

    assert metadata is not None
    assert metadata.name == tmp_path.name
