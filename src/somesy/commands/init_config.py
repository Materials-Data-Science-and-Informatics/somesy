"""CLI command to initialize somesy configuration file."""

import logging
from pathlib import Path

import tomlkit
from pydantic import BaseModel

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
            metadata,
            mode="json",
            by_alias=True,
            exclude_defaults=True,
            exclude_none=True,
        )
    }
    if config is not None:
        content["config"] = config.model_dump(mode="json", by_alias=True)
    with open(path, "w" if overwrite else "x", encoding="utf-8") as file:
        tomlkit.dump(content, file)


def init_config(input_path: Path, options: dict) -> None:
    """Initialize somesy configuration file.

    Args:
        input_path (Path): Path to somesy file (will be created/overwritten).
        options (dict): CLI options.

    """
    logger.info(f"Updating input file ({input_path}) with CLI configurations...")

    is_somesy = SomesyInput.is_somesy_file_path(input_path)
    if input_path.exists():
        # read directly: get_input_content refuses files without a somesy section
        with open(input_path, encoding="utf-8") as f:
            content = tomlkit.load(f)
    elif is_somesy:
        content = tomlkit.document()
    else:
        raise FileNotFoundError(f"Input file not found: {input_path}")

    input_file_type = "somesy" if is_somesy else "pyproject"
    msg = f"Found input file with {input_file_type} format."
    logger.log(VERBOSE, msg)

    logger.debug(f"Input file content: {options}")

    options.pop("input_file", None)
    if is_somesy:
        table = content
    else:
        if "tool" not in content:
            content["tool"] = tomlkit.table(is_super_table=True)
        if "somesy" not in content["tool"]:
            content["tool"]["somesy"] = tomlkit.table()
        table = content["tool"]["somesy"]
    # merge into the existing table, keeping keys that were not prompted for
    if "config" not in table:
        table["config"] = tomlkit.table()
    table["config"].update(options)

    with open(input_path, "w", encoding="utf-8") as f:
        tomlkit.dump(content, f)

    logger.info(f"Input file ({input_path}) updated.")
    logger.debug(f"Input file content: {content}")
