"""Pyproject core."""
import logging
from pathlib import Path
from typing import Union

import wrapt
from tomlkit import dump, load

from somesy.pyproject.poetry import Poetry
from somesy.pyproject.setuptools import SetupTools

logger = logging.getLogger("somesy")


class Pyproject(wrapt.ObjectProxy):
    """Class for syncing pyproject file with other metadata files."""

    def __init__(self, path: Path, create_if_not_exists: bool = False):
        """Pyproject wrapper class. Wraps either setuptools or poetry.

        Args:
            path (Path): Path to pyproject.toml file.
            create_if_not_exists (bool, optional): Create pyproject.toml file if not exists. Defaults to False.

        Raises:
            FileNotFoundError: Raised when pyproject.toml file is not found.
            ValueError: Neither project nor tool.poetry object is found in pyproject.toml file.
        """
        data = None
        # load the pyproject.toml file
        if not path.exists():
            if create_if_not_exists:
                path.touch()
                # if empty file is created, add tool.poetry object
                with open(path, "w") as f:
                    dump({"tool": {"poetry": {}}}, f)
            else:
                raise FileNotFoundError(f"pyproject file {path} not found")

        with open(path) as f:
            data = load(f)

        # setuptools has project object
        if "project" in data:
            logger.verbose("Found setuptools config in pyproject.toml file")  # type: ignore
            self.__wrapped__: Union[SetupTools, Poetry] = SetupTools(
                path, create_if_not_exists
            )
            super().__init__(self.__wrapped__)
        # poetry has tool.poetry object
        elif "tool" in data and "poetry" in data["tool"]:
            logger.verbose("Found poetry config in pyproject.toml file")  # type: ignore
            self.__wrapped__ = Poetry(path, create_if_not_exists)
            super().__init__(self.__wrapped__)
        # if no project object is found, but file exists, add tool.poetry object
        elif create_if_not_exists:
            logger.verbose(  # type: ignore
                "No config found in pyproject file, adding poetry config as default"
            )
            data = {"tool": {"poetry": {}}}
            with open(path, "w") as f:
                dump(data, f)
            self.__wrapped__ = Poetry(path, create_if_not_exists)
            super().__init__(self.__wrapped__)

        # value error if other project object is found
        else:
            raise ValueError(
                "pyproject file is invalid, either add project or tool.poetry object"
            )
