"""Utility functions for somesy."""
import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler
from tomlkit import TOMLDocument, load

from somesy.core.config import VERBOSE

logger = logging.getLogger("somesy")


def set_logger(debug: bool = False, verbose: bool = False, info: bool = False) -> None:
    """Set logger to rich handler and add custom logging level.

    Args:
        debug (bool): Debug mode, overrides verbose and info modes.
        verbose (bool): Verbose mode.
        info (bool): NO quiet mode, prints basic output.
    """
    logging.addLevelName(level=VERBOSE, levelName="VERBOSE")
    logger.propagate = False

    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(VERBOSE)
    elif info:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    def verbose_print(self, message, *args, **kwargs):
        """Verbose logging level print function."""
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, message.format(args), (), **kwargs)

    setattr(logging.Logger, "verbose", verbose_print)  # noqa: B010
    logging.basicConfig(
        format="%(message)s",
        datefmt="",
    )
    if not logger.handlers:
        logger.addHandler(
            RichHandler(
                show_time=False,
                rich_tracebacks=True,
                show_level=debug,
                show_path=debug,
                tracebacks_show_locals=debug,
                markup=True,
            )
        )


def load_somesy_content(input_path: Path) -> Optional[TOMLDocument]:
    """Load somesy file content if a valid file.

    Args:
        input_path (Path): input path. Must have somesy in the name and be a TOML file.

    Returns:
        Optional[TOMLDocument]: TOMLDocument object if the input file is a valid somesy input file, otherwise None
    """
    if input_path.suffix == ".toml" and "somesy" in input_path.name:
        with open(input_path, "r") as f:
            input_content = load(f)
            if "project" in input_content:
                return input_content

    return None


def load_pyproject_content(input_path: Path) -> Optional[TOMLDocument]:
    """Load pyproject file content if a valid file.

    Args:
        input_path (Path): input path. Must have pyproject in the name and be a TOML file.

    Returns:
        Optional[TOMLDocument]: TOMLDocument object if the input file is a valid pyproject input file, otherwise None
    """
    if input_path.suffix == ".toml" and "pyproject" in input_path.name:
        with open(input_path, "r") as f:
            input_content = load(f)
            if "tool" in input_content and "somesy" in input_content["tool"]:
                return input_content

    return None
