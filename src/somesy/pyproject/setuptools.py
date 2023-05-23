"""Setuptools config file handler parsed from pyproject.toml."""
import logging
from pathlib import Path
from typing import Any, List, Optional

from tomlkit import dump, inline_table, load, table

from somesy.core.models import Person, ProjectMetadataWriter
from somesy.pyproject.models import SetuptoolsConfig
from somesy.pyproject.utils import person_to_setuptools_dict

logger = logging.getLogger("somesy")


class SetupTools(ProjectMetadataWriter):
    """Setuptools config file handler parsed from setup.cfg."""

    def __init__(self, path: Path):
        """Setuptools config file handler parsed from pyproject.toml.

        Args:
            path (Path): Path to pyproject.toml file.
        """
        self.path = path
        self._load()
        self._validate()

    def _load(self) -> None:
        """Load pyproject.toml file."""
        if not self.path.exists():
            raise FileNotFoundError(f"pyproject file {self.path} not found")

        with open(self.path) as f:
            self._data = load(f)

    def _validate(self) -> None:
        """Validate setuptools config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        config = dict(self._data["project"])
        logger.debug(f"Validating setuptools config: {config}")
        SetuptoolsConfig(**config)

    def _get_property(self, key: str) -> Optional[Any]:
        """Get a property from the pyproject.toml file."""
        try:
            return self._data["project"][key]
        except KeyError:
            return None

    def _get_url(self, key: str) -> Optional[Any]:
        """Get a url object from setuptools config. If key is not found, return None."""
        try:
            return self._data["project"]["urls"][key]
        except KeyError:
            return None

    def __getitem__(self, key: str) -> Any:
        """Get value from setuptools config. If key is not found, return None."""
        try:
            return self._data["project"][key]
        except KeyError:
            return None

    def _set_property(self, key: str, value: Any) -> None:
        """Set a property in the pyproject.toml file."""
        if value:
            if key in ["authors", "maintainers"]:
                it = inline_table()
                it.add(key, value)
                self._data["project"].update(it)
            else:
                self._data["project"][key] = value

    def _set_url(self, key: str, value: Any) -> None:
        """Set a url object in setuptools config."""
        if value:
            if not ("urls" in self._data["project"]):
                self._data["project"]["urls"] = table()
            self._data["project"]["urls"][key] = value

    @property
    def authors(self) -> Optional[List[dict]]:
        """Get authors from setuptools config. If key is not found, return None."""
        return self._get_property("authors").unwrap()

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set authors in setuptools config."""
        if authors:
            self._set_property(
                "authors", [person_to_setuptools_dict(c) for c in authors]
            )

    @property
    def maintainers(self) -> Optional[List[dict]]:
        """Get maintainers from setuptools config. If key is not found, return None."""
        return self._get_property("maintainers").unwrap()

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set maintainers in setuptools config."""
        if maintainers:
            self._set_property(
                "maintainers", ([person_to_setuptools_dict(c) for c in maintainers])
            )

    @property
    def homepage(self) -> Optional[str]:
        """Get homepage url from setuptools config. If key is not found, return None."""
        return self._get_url("homepage")

    @homepage.setter
    def homepage(self, homepage: Optional[str]) -> None:
        """Set homepage url in setuptools config."""
        self._set_url("homepage", homepage)

    @property
    def repository(self) -> Optional[str]:
        """Get repository url from setuptools config. If key is not found, return None."""
        return self._get_url("repository")

    @repository.setter
    def repository(self, repository: Optional[str]) -> None:
        """Set repository url in setuptools config."""
        self._set_url("repository", repository)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the pyproject file using instance."""
        if path:
            with open(path, "w") as f:
                dump(self._data, f)
        else:
            with open(self.path, "w") as f:
                dump(self._data, f)
