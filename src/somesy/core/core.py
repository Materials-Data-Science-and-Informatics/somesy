"""Core somesy functions."""
import logging
from pathlib import Path
from typing import Optional

from tomlkit import TOMLDocument

from somesy.core.models import ProjectMetadata, SomesyConfig
from somesy.core.utils import load_pyproject_content, load_somesy_content

logger = logging.getLogger("somesy")


def get_project_metadata(path: Path) -> ProjectMetadata:
    """Return project metadata to from different sources as a simple dict. Currently, only pyproject.toml inputs are supported.

    Args:
        path (Path): input source path

    Returns:
        project metadata input to sync output files
    """
    content = get_input_content(path)
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
    content = get_input_content(path)
    return _extract_cli_config(content)


def get_input_content(path: Path) -> TOMLDocument:
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
