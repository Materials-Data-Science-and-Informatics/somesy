"""Poetry config file handler parsed from pyproject.toml."""
import logging
from pathlib import Path
from typing import Any, List, Optional

from tomlkit import dump, load

from somesy.core.models import Person, ProjectMetadataOutputWrapper
from somesy.pyproject.models import PoetryConfig
from somesy.pyproject.utils import person_to_poetry_string

logger = logging.getLogger("somesy")


class Poetry(ProjectMetadataOutputWrapper):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(self, path: Path, create_if_not_exists: bool = False):
        """Poetry config file handler parsed from pyproject.toml.

        Args:
            path (Path): Path to pyproject.toml file.
            create_if_not_exists (bool, optional): Create pyproject.toml file if not exists. Defaults to False.
        """
        self.path = path
        self.create_if_not_exists = create_if_not_exists
        self._load()
        self._validate()

    def _load(self) -> None:
        """Load pyproject.toml file."""
        if not self.path.exists():
            if self.create_if_not_exists:
                self._create_empty_file()
            else:
                raise FileNotFoundError(f"pyproject file {self.path} not found")
        else:
            with open(self.path) as f:
                self._data = load(f)

        # create a Poetry object if it doesn't exist
        if not ("tool" in self._data and "poetry" in self._data["tool"]):
            self._data["tool"]["poetry"] = {}

    def _validate(self) -> None:
        """Validate poetry config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        config = dict(self._data["tool"]["poetry"])
        logger.debug(f"Validating poetry config: {config}")
        if config:
            PoetryConfig(**config)

    def _get_property(self, key: str) -> Optional[Any]:
        """Get a property from the pyproject.toml file."""
        try:
            return self._data["tool"]["poetry"][key]
        except KeyError:
            return None

    def __getitem__(self, key: str) -> Any:
        """Get a property from the pyproject.toml file."""
        try:
            return self._data["tool"]["poetry"][key]
        except KeyError:
            return None

    def _set_property(self, key: str, value: Any) -> None:
        """Set a property in the pyproject.toml file."""
        if value:
            self._data["tool"]["poetry"][key] = value

    @property
    def authors(self) -> Optional[List[str]]:
        """Project authors."""
        return self._get_property("authors")

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set project authors."""
        if authors:
            self._set_property("authors", [person_to_poetry_string(c) for c in authors])

    @property
    def maintainers(self) -> Optional[List[str]]:
        """Project maintainers."""
        return self._get_property("maintainers")

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set project maintainers."""
        if maintainers:
            self._set_property(
                "maintainers", [person_to_poetry_string(c) for c in maintainers]
            )

    def dump(self, path: Optional[Path] = None) -> None:
        """Dump the pyproject file using instance."""
        if path:
            with open(path, "w") as f:
                dump(self._data, f)
        else:
            with open(self.path, "w") as f:
                dump(self._data, f)
