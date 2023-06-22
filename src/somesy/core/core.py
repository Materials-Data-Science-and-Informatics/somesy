"""Core somesy functions."""
import logging
from pathlib import Path
from typing import Optional

import tomlkit
from tomlkit import TOMLDocument

from somesy.core.models import ProjectMetadata, SomesyConfig

logger = logging.getLogger("somesy")


def load_somesy_content(input_path: Path) -> Optional[TOMLDocument]:
    """Load somesy file content if a valid file.

    Args:
        input_path (Path): input path. Must have somesy in the name and be a TOML file.

    Returns:
        TOMLDocument object if the input file is a valid somesy input file, otherwise None
    """
    if input_path.suffix == ".toml" and "somesy" in input_path.name:
        with open(input_path, "r") as f:
            input_content = tomlkit.load(f)
            if "project" in input_content:
                return input_content

    return None


def load_pyproject_content(input_path: Path) -> Optional[TOMLDocument]:
    """Load pyproject file content if a valid file.

    Args:
        input_path (Path): input path. Must have pyproject in the name and be a TOML file.

    Returns:
        TOMLDocument object if the input file is a valid pyproject input file, otherwise None
    """
    if input_path.suffix == ".toml" and "pyproject" in input_path.name:
        with open(input_path, "r") as f:
            input_content = tomlkit.load(f)
            if "tool" in input_content and "somesy" in input_content["tool"]:
                return input_content

    return None


def get_project_metadata(path: Path) -> ProjectMetadata:
    """Return project metadata to from different sources as a simple dict. Currently, only pyproject.toml inputs are supported.

    Args:
        path (Path): input source path

    Returns:
        project metadata input to sync output files
    """
    content = _get_input_content(path)
    return _extract_metadata(content)


def get_somesy_cli_config(path: Path) -> Optional[SomesyConfig]:
    """Load somesy cli config from config file.

    Given a path to a TOML file, this function reads the file and extracts the somesy config from it.
    If the input file is not a valid somesy input file or if the file is not a TOML file, the function raises a ValueError.

    Args:
        path (Path): path to the input file

    Returns:
        somesy config if it exists in the input file, otherwise None
    """
    content = _get_input_content(path)
    return _extract_cli_config(content)


def validate_somesy_input(input_file: Path) -> bool:
    """Validate somesy input file.

    Args:
        input_file (Path): input file path

    Returns:
        True if the input file is a valid somesy input file, otherwise False
    """
    # validate project metadata
    try:
        get_project_metadata(input_file)
    except Exception as e:
        logger.warning(f"Error on project metadata validation:\n{e}")
        return False

    # validate somesy cli config
    try:
        get_somesy_cli_config(input_file)
    except Exception as e:
        logger.warning(f"Error on cli config validation:\n{e}")
        return False

    return True


# ----


def _get_input_content(path: Path) -> TOMLDocument:
    """Read contents of a somesy input file.

    Given a path to a TOML file, this function reads the file and returns its content as a TOMLDocument object.
    The function checks if the file is a valid somesy input file by checking its name and content.
    If the file is not a valid somesy input file, the function raises a ValueError.

    Args:
        path (Path): path to the input file

    Returns:
        the content of the input file as a TOMLDocument object

    Raises:
        ValueError: if the input file is not a valid somesy input file or if the file is not a TOML file.
    """
    input_content = load_somesy_content(path)
    if input_content is not None:
        return input_content

    input_content = load_pyproject_content(path)
    if input_content is not None:
        return input_content["tool"]["somesy"]
    else:
        raise ValueError("Unsupported input file.")


def _extract_metadata(content: TOMLDocument) -> ProjectMetadata:
    """Extract metadata from TOMLDocument.

    Args:
        content (TOMLDocument): TOMLDocument object

    Returns:
        project metadata
    """
    metadata = content["project"]
    try:
        metadata = metadata.unwrap()
        return ProjectMetadata(**metadata)
    except Exception as e:
        raise ValueError(f"Somesy input validation failed: {e}")


def _extract_cli_config(content: TOMLDocument) -> Optional[SomesyConfig]:
    """Extract config from TOMLDocument.

    Args:
        content (TOMLDocument): TOMLDocument object

    Returns:
        somesy config
    """
    if (
        "config" in content
        and "cli" in content["config"]
        and content["config"]["cli"] != ""
    ):
        config = content["config"]["cli"]
        try:
            config = config.unwrap()
            return SomesyConfig(**config)
        except Exception as e:
            raise ValueError(f"Somesy config validation failed: {e}")
    else:
        return None
