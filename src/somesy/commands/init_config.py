"""CLI command to initialize somesy configuration file."""
import logging
from pathlib import Path

from tomlkit import TOMLDocument, dump

from somesy.cli.models import SyncCommandOptions
from somesy.core.utils import load_pyproject_content, load_somesy_content

logger = logging.getLogger("somesy")


def init_config(input_path: Path, options: SyncCommandOptions) -> None:
    """Initialize somesy configuration file.

    Args:
        input_path (Path): Path to somesy file.
        options (SyncCommandOptions): CLI options.
    """
    logger.info(f"Updating input file ({input_path}) with CLI configurations...")
    content, is_somesy = _load(input_path)
    logger.verbose(
        f"Found input file with {'somesy' if is_somesy else 'pyproject'} format."
    )
    options_dict = options.asdict(remove_keys=["input_file"])
    logger.debug(f"Input file content: {options_dict}")

    if is_somesy:
        content["config"] = {"cli": options_dict}
    else:
        content["tool"]["somesy"]["config"] = {"cli": options_dict}

    with open(input_path, "w") as f:
        dump(content, f)

    logger.info(f"Input file ({input_path}) updated.")
    logger.debug(f"Input file content: {content}")


def _load(input_path: Path) -> tuple[TOMLDocument, bool]:
    """Load somesy file content if a valid file.

    Args:
        input_path (Path): Path to somesy file.

    Raises:
        Exception: If the file is not a valid somesy file.

    Returns: A tuple with:
        TOMLDocument: content of the file.
        bool: True if the file is a somesy file, False if it is a pyproject file.
    """
    content = load_somesy_content(input_path)
    if content is not None:
        return content, True

    content = load_pyproject_content(input_path)
    if content is not None:
        return content, False
    else:
        raise ValueError("Input file is invalid.")
