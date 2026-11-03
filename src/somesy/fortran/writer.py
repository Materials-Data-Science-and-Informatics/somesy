"""Fortran writer."""

import logging
from pathlib import Path

import tomlkit
from rich.pretty import pretty_repr

from somesy.core.models import Entity, Person, ProjectMetadata, parse_name_email
from somesy.core.writer import (
    FieldKeyMapping,
    IgnoreKey,
    ProjectMetadataWriter,
    format_toml_data,
    license_expression,
)

from .models import FortranConfig

logger = logging.getLogger("somesy")


class Fortran(ProjectMetadataWriter):
    """Fortran config file handler parsed from fpm.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: bool | None = False,
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
        author = self._get_property(self._get_key("authors"))
        return [author] if author else []

    @authors.setter
    def authors(self, authors: list[Person | Entity]) -> None:
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
    def maintainers(self, maintainers: list[Person | Entity]) -> None:
        """Set the maintainers of the project."""
        maintainer = self._from_person(maintainers[0])
        self._set_property(self._get_key("maintainers"), maintainer)

    def _load(self) -> None:
        """Load fpm.toml file."""
        with open(self.path, encoding="utf-8") as f:
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

    def save(self, path: Path | None = None) -> None:
        """Save the fpm file."""
        path = path or self.path
        format_toml_data(self._data)

        with open(path, "w", encoding="utf-8") as f:
            tomlkit.dump(self._data, f)

    @staticmethod
    def _from_person(person: Person | Entity):
        """Convert project metadata person/entity object to poetry string for person format "full name <email>."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person_obj: str) -> Person | Entity | None:
        """Convert from free string to person or entity object."""
        return parse_name_email(person_obj)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        if metadata.name is not None:
            self.name = metadata.name
        if metadata.description is not None:
            self.description = metadata.description

        if metadata.version:
            self.version = metadata.version

        if metadata.keywords:
            self.keywords = metadata.keywords

        if metadata.authors():
            self.authors = metadata.authors()
        maintainers = metadata.maintainers()

        # set if not empty
        if maintainers:
            # only one maintainer is allowed
            self.maintainers = maintainers

        if licenses := metadata.license:
            self.license = license_expression(licenses)

        if metadata.homepage:
            self.homepage = str(metadata.homepage)
