"""CLI command to initialize somesy configuration file."""

import logging
from pathlib import Path

import tomlkit

from somesy.core.core import get_input_content
from somesy.core.models import SomesyInput

logger = logging.getLogger("somesy")


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
    logger.verbose(msg)

    logger.debug(f"Input file content: {options}")

    if "input_file" in options:
        del options["input_file"]
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
