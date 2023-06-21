"""Setuptools config file handler parsed from pyproject.toml."""
from pathlib import Path
from typing import Optional

from somesy.core.models import Person
from somesy.pyproject.common import PyprojectCommon
from somesy.pyproject.models import SetuptoolsConfig


class SetupTools(PyprojectCommon):
    """Setuptools config file handler parsed from setup.cfg."""

    def __init__(self, path: Path):
        """Setuptools config file handler parsed from pyproject.toml.

        See [somesy.core.models.ProjectMetadataWriter.__init__][].
        """
        super().__init__(path, section=["project"], model_cls=SetuptoolsConfig)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to setuptools dict for person format."""
        return {"name": person.full_name, "email": person.email}

    # ----

    @property
    def homepage(self) -> Optional[str]:
        """Get homepage url from setuptools config. If key is not found, return None."""
        return self._get_property(["urls", "homepage"])

    @homepage.setter
    def homepage(self, homepage: Optional[str]) -> None:
        """Set homepage url in setuptools config."""
        self._set_property(["urls", "homepage"], homepage)

    @property
    def repository(self) -> Optional[str]:
        """Get repository url from setuptools config. If key is not found, return None."""
        return self._get_property(["urls", "repository"])

    @repository.setter
    def repository(self, repository: Optional[str]) -> None:
        """Set repository url in setuptools config."""
        self._set_property(["urls", "repository"], repository)
