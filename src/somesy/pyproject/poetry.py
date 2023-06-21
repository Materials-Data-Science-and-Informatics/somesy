"""Poetry config file handler parsed from pyproject.toml."""
from pathlib import Path

from somesy.core.models import Person
from somesy.pyproject.common import PyprojectCommon
from somesy.pyproject.models import PoetryConfig


class Poetry(PyprojectCommon):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(self, path: Path):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.models.ProjectMetadataWriter.__init__][].
        """
        super().__init__(path, section=["tool", "poetry"], model_cls=PoetryConfig)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to poetry string for person format "full name <email>."""
        return f"{person.full_name} <{person.email}>"
