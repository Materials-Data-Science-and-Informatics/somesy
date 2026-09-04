"""Harvest metadata from supported project files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from somesy.fortran.writer import Fortran
from somesy.julia.writer import Julia
from somesy.mkdocs.writer import MkDocs
from somesy.package_json.writer import PackageJSON
from somesy.pom_xml.writer import POM
from somesy.pyproject.writer import Pyproject
from somesy.rust.writer import Rust

logger = logging.getLogger("somesy")

_SOURCES = (
    ("pyproject.toml", Pyproject),
    ("package.json", PackageJSON),
    ("Project.toml", Julia),
    ("fpm.toml", Fortran),
    ("Cargo.toml", Rust),
    ("pom.xml", POM),
    ("mkdocs.yml", MkDocs),
)


def harvest_sources(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Read all supported non-generated metadata files under ``root``."""
    sources = []
    for filename, writer_cls in _SOURCES:
        path = root / filename
        if not path.is_file():
            continue
        try:
            writer = writer_cls(path, pass_validation=True)
            sources.append((path, writer.harvest_metadata()))
        except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
            logger.warning("Cannot harvest metadata from %s: %s", path, error)
    return sources
