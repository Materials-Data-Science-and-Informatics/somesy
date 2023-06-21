"""Setuptools config file handler parsed from pyproject.toml."""
from pathlib import Path

from somesy.core.models import Person
from somesy.pyproject.common import PyprojectCommon
from somesy.pyproject.models import SetuptoolsConfig


class SetupTools(PyprojectCommon):
    """Setuptools config file handler parsed from setup.cfg."""

    def __init__(self, path: Path):
        """Setuptools config file handler parsed from pyproject.toml.

        See [somesy.core.models.ProjectMetadataWriter.__init__][].
        """
        section = ["project"]
        mappings = {
            "homepage": ["urls", "homepage"],
            "repository": ["urls", "repository"],
        }
        super().__init__(
            path, section=section, direct_mappings=mappings, model_cls=SetuptoolsConfig
        )

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to setuptools dict for person format."""
        return {"name": person.full_name, "email": person.email}
