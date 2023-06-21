"""Common part of pyproject and setuptools-based pyproject.toml writers."""
import logging
from pathlib import Path
from typing import Any, List, Optional, Union

import tomlkit
from rich.pretty import pretty_repr

from somesy.core.writer import ProjectMetadataWriter

logger = logging.getLogger("somesy")


class PyprojectCommon(ProjectMetadataWriter):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(
        self, path: Path, *, section: List[str], model_cls, direct_mappings=None
    ):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.models.ProjectMetadataWriter.__init__][].
        """
        self._model_cls = model_cls
        self._section = section
        super().__init__(
            path, create_if_not_exists=False, direct_mappings=direct_mappings or {}
        )

    def _load(self) -> None:
        """Load pyproject.toml file."""
        with open(self.path) as f:
            self._data = tomlkit.load(f)

    def _validate(self) -> None:
        """Validate poetry config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {self._model_cls.__name__}: {pretty_repr(config)}"
        )
        self._model_cls(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the pyproject file."""
        path = path or self.path
        with open(path, "w") as f:
            tomlkit.dump(self._data, f)

    def _get_property(self, key: Union[str, List[str]]) -> Optional[Any]:
        """Get a property from the pyproject.toml file."""
        key_path = [key] if isinstance(key, str) else key
        full_path = self._section + key_path
        return super()._get_property(full_path)

    def _set_property(self, key: Union[str, List[str]], value: Any) -> None:
        """Set a property in the pyproject.toml file."""
        key_path = [key] if isinstance(key, str) else key
        # get the tomlkit object of the section
        dat = self._get_property([])
        # dig down, create missing nested objects on the fly
        curr = dat
        for key in key_path[:-1]:
            if key not in curr:
                curr.add(key, tomlkit.table())
            curr = curr[key]
        curr[key_path[-1]] = value
