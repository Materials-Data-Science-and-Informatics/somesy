"""Core somesy functions."""
from pathlib import Path
from typing import Optional

from tomlkit import TOMLDocument, load

from somesy.core.models import ProjectMetadata, SomesyCLIConfig


def get_project_metadata(path: Path) -> ProjectMetadata:
    """Return project metadata to from different sources as a simple dict. Currently, only pyproject.toml inputs are supported.

    Args:
        path (Path): input source path

    Returns:
        ProjectMetadata: project metadata input to sync output files
    """
    content = get_input_content(path)
    return _extract_metadata(content)


def get_somesy_cli_config(path: Path) -> Optional[SomesyCLIConfig]:
    """Load somesy cli config from config file.

    Given a path to a TOML file, this function reads the file and extracts the somesy config from it.
    If the input file is not a valid somesy input file or if the file is not a TOML file, the function raises a ValueError.

    Args:
        path (Path): path to the input file

    Returns:
        Optional[SomesyCLIConfig]: somesy config if it exists in the input file, otherwise None
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
        TOMLDocument: the content of the input file as a TOMLDocument object

    Raises:
        ValueError: if the input file is not a valid somesy input file or if the file is not a TOML file.
    """
    if path.suffix == ".toml":
        with open(path, "r") as f:
            input_content = load(f)

        # load project metadata
        if "somesy" in path.name and "project" in input_content:
            return input_content

        elif (
            "pyproject" in path.name
            and "tool" in input_content
            and "somesy" in input_content["tool"]
            and "project" in input_content["tool"]["somesy"]
        ):
            return input_content["tool"]["somesy"]
        else:
            raise ValueError("Somesy input not found.")
    else:
        raise ValueError("Only toml files are supported for reading somesy input.")


def _extract_metadata(content: TOMLDocument) -> ProjectMetadata:
    """Extract metadata from TOMLDocument.

    Args:
        content (TOMLDocument): TOMLDocument object

    Returns:
        ProjectMetadata: project metadata
    """
    metadata = content["project"]
    try:
        metadata = metadata.unwrap()
        return ProjectMetadata(**metadata)
    except Exception as e:
        raise ValueError(f"Somesy input validation failed: {e}")


def _extract_cli_config(content: TOMLDocument) -> Optional[SomesyCLIConfig]:
    """Extract config from TOMLDocument.

    Args:
        content (TOMLDocument): TOMLDocument object

    Returns:
        Optional[SomesyCLIConfig]: somesy config
    """
    if (
        "config" in content
        and "cli" in content["config"]
        and content["config"]["cli"] != ""
    ):
        config = content["config"]["cli"]
        try:
            config = config.unwrap()
            return SomesyCLIConfig(**config)
        except Exception as e:
            raise ValueError(f"Somesy config validation failed: {e}")
    else:
        return None
