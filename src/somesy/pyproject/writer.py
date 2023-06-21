"""Pyproject core."""
import logging
from pathlib import Path
from typing import Union

import wrapt
from tomlkit import load

from somesy.pyproject.poetry import Poetry
from somesy.pyproject.setuptools import SetupTools

logger = logging.getLogger("somesy")


class Pyproject(wrapt.ObjectProxy):
    """Class for syncing pyproject file with other metadata files."""

    __wrapped__: Union[SetupTools, Poetry]

    def __init__(self, path: Path):
        """Pyproject wrapper class. Wraps either setuptools or poetry.

        Args:
            path (Path): Path to pyproject.toml file.

        Raises:
            FileNotFoundError: Raised when pyproject.toml file is not found.
            ValueError: Neither project nor tool.poetry object is found in pyproject.toml file.
        """
        data = None
        if not path.is_file():
            raise FileNotFoundError(f"pyproject file {path} not found")

        with open(path, "r") as f:
            data = load(f)

        # inspect file to pick suitable project metadata writer
        if "project" in data:
            logger.verbose("Found setuptools-based metadata in pyproject.toml")
            self.__wrapped__ = SetupTools(path)
        elif "tool" in data and "poetry" in data["tool"]:
            logger.verbose("Found poetry-based metadata in pyproject.toml")
            self.__wrapped__ = Poetry(path)
        else:
            msg = "The pyproject.toml file is ambiguous, either add a [project] or [tool.poetry] section"
            raise ValueError(msg)

        super().__init__(self.__wrapped__)
