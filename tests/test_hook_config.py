"""Tests for the pre-commit hook configuration."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent


def _files_regex(config: Path, hook_id: str) -> str:
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    hooks = (
        data
        if isinstance(data, list)
        else [h for r in data["repos"] for h in r["hooks"]]
    )
    return next(h["files"] for h in hooks if h["id"] == hook_id)


def test_local_hook_is_copy_of_published_hook():
    published = _files_regex(ROOT / ".pre-commit-hooks.yaml", "somesy")
    local = _files_regex(ROOT / ".pre-commit-config.yaml", "somesy-sync")
    assert published == local


@pytest.mark.parametrize(
    "path,expected",
    [
        ("somesy.toml", True),
        (".somesy.toml", True),
        ("pyproject.toml", True),
        ("package.json", True),
        ("Project.toml", True),
        ("Cargo.toml", True),
        ("fpm.toml", True),
        ("pkg/somesy.toml", True),
        ("packages/a/Cargo.toml", True),
        ("README.md", False),
        ("cargo.toml", False),
        ("mysomesy.toml", False),
        ("pyproject.toml.bak", False),
        ("docs/package.json.md", False),
    ],
)
def test_hook_files_regex(path, expected):
    regex = _files_regex(ROOT / ".pre-commit-hooks.yaml", "somesy")
    assert bool(re.search(regex, path)) is expected
