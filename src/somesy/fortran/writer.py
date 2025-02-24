"""Fortran writer."""

import logging
from pathlib import Path
from typing import List, Optional, Union

import tomlkit
from rich.pretty import pretty_repr

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, IgnoreKey, ProjectMetadataWriter

from .models import FortranConfig

logger = logging.getLogger("somesy")


class Fortran(ProjectMetadataWriter):
    """Fortran config file handler parsed from fpm.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: Optional[bool] = False,
    ):
        """Fortran config file handler parsed from fpm.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        mappings: FieldKeyMapping = {
            "authors": ["author"],
            "maintainers": ["maintainer"],
            "documentation": IgnoreKey(),
        }
        super().__init__(
            path,
            create_if_not_exists=False,
            direct_mappings=mappings,
            pass_validation=pass_validation,
        )

    @property
    def authors(self):
        """Return the only author of the fpm.toml file as list."""
        authors = []
        try:
            self._to_person(self._get_property(self._get_key("authors")))
            authors = [self._get_property(self._get_key("authors"))]
        except ValueError:
            logger.warning("Cannot convert authors to Person object.")
        return authors

    @authors.setter
    def authors(self, authors: List[Union[Person, Entity]]) -> None:
        """Set the authors of the project."""
        self._set_property(self._get_key("authors"), self._from_person(authors[0]))

    @property
    def maintainers(self):
        """Return the only author of the fpm.toml file as list."""
        maintainers = self._get_property(self._get_key("maintainers"))
        if maintainers:
            return [self._get_property(self._get_key("maintainers"))]
        return []

    @maintainers.setter
    def maintainers(self, maintainers: List[Union[Person, Entity]]) -> None:
        """Set the maintainers of the project."""
        maintainers = self._from_person(maintainers[0])
        self._set_property(self._get_key("maintainers"), maintainers)

    def _load(self) -> None:
        """Load fpm.toml file."""
        with open(self.path) as f:
            self._data = tomlkit.load(f)

    def _validate(self) -> None:
        """Validate poetry config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        if self.pass_validation:
            return
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {FortranConfig.__name__}: {pretty_repr(config)}"
        )
        FortranConfig(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the fpm file."""
        path = path or self.path
        with open(path, "w") as f:
            tomlkit.dump(self._data, f)

    @staticmethod
    def _from_person(person: Union[Person, Entity]):
        """Convert project metadata person/entity object to poetry string for person format "full name <email>."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person: str) -> Optional[Union[Person, Entity]]:
        """Convert from free string to person or entity object."""
        try:
            return Person.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.info(f"Cannot convert {person} to Person object, trying Entity.")

        try:
            return Entity.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person} to Entity.")
            return None

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        self.name = metadata.name
        self.description = metadata.description

        if metadata.version:
            self.version = metadata.version

        if metadata.keywords:
            self.keywords = metadata.keywords

        self.authors = metadata.authors()
        maintainers = metadata.maintainers()

        # set if not empty
        if maintainers:
            # only one maintainer is allowed
            self.maintainers = maintainers

        self.license = metadata.license.value

        self.homepage = str(metadata.homepage) if metadata.homepage else None
