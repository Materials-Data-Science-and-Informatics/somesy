"""Harvest project metadata from a Git repository."""

from __future__ import annotations

import logging
import shutil
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

from .models import GitAuthor, GitMetadata

logger = logging.getLogger("somesy")


def _git(path: Path, *args: str) -> str:
    """Run Git without invoking a shell."""
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git executable not found")
    result = subprocess.run(  # noqa: S603 - arguments are fixed internal Git commands
        [git, *args],
        cwd=path,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _remote(path: Path) -> str | None:
    """Return the origin URL, or the first configured remote URL."""
    try:
        return _git(path, "remote", "get-url", "origin")
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            remotes = _git(path, "remote").splitlines()
            return _git(path, "remote", "get-url", remotes[0]) if remotes else None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


def _authors(path: Path) -> list[GitAuthor]:
    """Return all distinct mailmap-aware Git authors, ranked by commit count."""
    try:
        raw = _git(path, "log", "--all", "--format=%aN%x00%aE")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    identities = []
    for record in raw.splitlines():
        name, _, email = record.partition("\x00")
        if name:
            identities.append((name, email or None))

    counts = Counter(identities)
    return [
        GitAuthor(name=name, email=email, commit_count=count)
        for (name, email), count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def _date(path: Path, *args: str) -> date | None:
    """Return a Git date, if the requested revision exists."""
    try:
        value = _git(path, *args)
        return date.fromisoformat(value.splitlines()[0]) if value else None
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None


def _is_shallow(path: Path) -> bool:
    """Return whether Git history is incomplete."""
    try:
        return _git(path, "rev-parse", "--is-shallow-repository") == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def harvest(path: Path = Path.cwd()) -> GitMetadata | None:
    """Harvest Somesy-relevant metadata from ``path`` if it is a Git repository."""
    try:
        root = Path(_git(path, "rev-parse", "--show-toplevel"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    try:
        version = _git(root, "describe", "--tags", "--abbrev=0") or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        version = None

    shallow = _is_shallow(root)
    if shallow:
        logger.warning(
            "Git history is shallow; omitting dateCreated. Fetch full history to enrich it."
        )

    return GitMetadata(
        name=root.name,
        repository=_remote(root),
        version=version,
        date_created=None
        if shallow
        else _date(root, "log", "--reverse", "--format=%cs"),
        date_modified=_date(root, "log", "-1", "--format=%cs"),
        authors=_authors(root),
    )
