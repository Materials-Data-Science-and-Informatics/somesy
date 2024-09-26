"""Poetry based codemeta.json enhancement."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from somesy.pyproject.writer import Poetry

from .common import convert_dependencies

logger = logging.getLogger("somesy")
# TODO: tests


def enhance_with_poetry(codemeta: dict, pyproject_file: Path):
    """Enhance project metadata with poetry and setuptools information.

    Args:
        codemeta: Codemeta metadata to enhance.
        pyproject_file: Poetry config file handler parsed from pyproject.toml.

    Returns:
        Enhanced project metadata.

    """
    try:
        poetry = Poetry(pyproject_file)

    except Exception as e:
        logger.error(f"Failed to load Poetry configuration: {e}")
        return codemeta

    # direct mapping
    codemeta["runtimePlatform"] = "Python 3"

    # add dependency information
    if (deps := _process_deps(poetry)) is not None:
        codemeta["softwareRequirements"] = deps

    # add readme information
    if (readme := _process_readme(poetry)) is not None:
        codemeta["readme"] = readme

    return codemeta


def _process_readme(poetry: Poetry) -> Optional[str]:
    """Return a valid readme string if it is an URL.

    Args:
        poetry (Poetry): Poetry object.

    Returns:
        Optional[str]: valid URL for readme

    """
    data = poetry._data["tool"]["poetry"]
    if (readme := data.get("readme", None)) is not None:
        readme = str(readme)
        if readme.startswith("http"):
            return readme

    return None


def _process_deps(poetry: Poetry):
    try:
        dependencies = poetry.dependencies
        simplified_deps = _simplify_poetry_deps(dependencies)
        converted_dependencies = convert_dependencies(simplified_deps, "Python 3")
        return converted_dependencies
    except Exception as e:
        logger.warning(f"Codemeta enhancing on python dependencies failed: {e}")
        return None


def _simplify_poetry_deps(
    dependencies: Dict[str, Union[str, Dict[str, Union[str, List[str]]]]],
) -> Dict[str, str]:
    response = {}
    for key in dependencies.keys():
        value = dependencies[key]
        if key.lower() == "python":
            continue

        if isinstance(value, str):
            response[key] = value
        else:
            response[key] = value.get("version", "")
    return response
