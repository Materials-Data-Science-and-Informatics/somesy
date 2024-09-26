"""Enhance codemeta.json by harvesting data."""

from pathlib import Path
from typing import Optional

from .poetry import enhance_with_poetry

# TODO: tests


def enhance(codemeta: dict, pyproject_file: Optional[Path] = None) -> dict:
    """Enhance project metadata with poetry and setuptools information.

    Args:
        codemeta (dict): codemeta dictionary to enhance.
        pyproject_file (Optional[Path]): pyproject.toml location.

    Returns:
        Enhanced project metadata.

    """
    if pyproject_file:
        codemeta = enhance_with_poetry(codemeta, pyproject_file)

    # direct mapping
    codemeta["identifier"] = codemeta["name"]

    return codemeta


__all__ = ["enhance"]
