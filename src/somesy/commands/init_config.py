"""CLI command to initialize somesy configuration file."""

import logging
from pathlib import Path

import tomlkit
from pydantic import BaseModel

from somesy.core.core import get_input_content
from somesy.core.log import VERBOSE
from somesy.core.models import ProjectMetadata, SomesyConfig, SomesyInput

logger = logging.getLogger("somesy")


def write_somesy_file(
    metadata: ProjectMetadata,
    path: Path = Path("somesy.toml"),
    *,
    config: SomesyConfig | None = None,
    overwrite: bool = False,
) -> None:
    """Write project metadata to a standalone ``somesy.toml`` file."""
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {path}")

    content = {
        "project": BaseModel.model_dump(
            metadata, mode="json", by_alias=True, exclude_none=True
        )
    }
    if config is not None:
        content["config"] = config.model_dump(mode="json", by_alias=True)
    with open(path, "w" if overwrite else "x") as file:
        tomlkit.dump(content, file)


def init_config(input_path: Path, options: dict) -> None:
    """Initialize somesy configuration file.

    Args:
        input_path (Path): Path to somesy file (will be created/overwritten).
        options (dict): CLI options.

    """
    logger.info(f"Updating input file ({input_path}) with CLI configurations...")

    content = get_input_content(input_path, no_unwrap=True)

    is_somesy = SomesyInput.is_somesy_file_path(input_path)
    input_file_type = "somesy" if is_somesy else "pyproject"
    msg = f"Found input file with {input_file_type} format."
    logger.log(VERBOSE, msg)

    logger.debug(f"Input file content: {options}")

    options.pop("input_file", None)
    if is_somesy:
        content["config"] = options
    else:
        if "tool" not in content:
            content["tool"] = {}
        if "somesy" not in content["tool"]:
            content["tool"]["somesy"] = {}
        content["tool"]["somesy"]["config"] = options

    with open(input_path, "w") as f:
        tomlkit.dump(content, f)

    logger.info(f"Input file ({input_path}) updated.")
    logger.debug(f"Input file content: {content}")
