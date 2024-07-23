"""Julia writer."""

import logging
from pathlib import Path
from typing import List, Optional

import tomlkit
from rich.pretty import pretty_repr

from somesy.core.models import Person, ProjectMetadata
from somesy.core.writer import ProjectMetadataWriter

from .models import JuliaConfig

logger = logging.getLogger("somesy")


class Julia(ProjectMetadataWriter):
    """Julia config file handler parsed from Project.toml."""

    def __init__(self, path: Path):
        """Julia config file handler parsed from Project.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        super().__init__(path, create_if_not_exists=False)

    def _load(self) -> None:
        """Load Project.toml file."""
        with open(self.path) as f:
            self._data = tomlkit.load(f)

    def _validate(self) -> None:
        """Validate poetry config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {JuliaConfig.__name__}: {pretty_repr(config)}"
        )
        JuliaConfig(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the julia file."""
        path = path or self.path
        with open(path, "w") as f:
            tomlkit.dump(self._data, f)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to a name+email string."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person_obj: str) -> Person:
        """Parse name+email string to a Person."""
        return Person.from_name_email_string(person_obj)

    @property
    def authors(self) -> List[str]:
        """Get authors from the pyproject.toml file."""
        # check if authors can be converted to person, only return valid ones
        authors = self._get_property("authors")
        if authors is None:
            return []

        valid_authors = []
        for author in authors:
            try:
                self._to_person(author)
                valid_authors.append(author)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid author format: {author}")
        return valid_authors

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set the authors of the project."""
        authors = [self._from_person(c) for c in authors]
        self._set_property(self._get_key("authors"), authors)

    @property
    def maintainers(self) -> List[str]:
        """Get maintainers from the pyproject.toml file."""
        # check if maintainers can be converted to person, only return valid ones
        maintainers = self._get_property("maintainers")
        if maintainers is None:
            return []

        valid_maintainers = []
        for maintainer in maintainers:
            try:
                self._to_person(maintainer)
                valid_maintainers.append(maintainer)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid maintainer format: {maintainer}")
        return valid_maintainers

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set the maintainers of the project."""
        maintainers = [self._from_person(c) for c in maintainers]
        self._set_property(self._get_key("maintainers"), maintainers)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        # overridden to not sync fields that are not present in the Project.toml file
        self.name = metadata.name
        self.version = metadata.version

        self._sync_authors(metadata)
