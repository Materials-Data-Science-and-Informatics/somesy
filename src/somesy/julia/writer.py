"""Julia writer."""

import logging
from pathlib import Path

import tomlkit
from rich.pretty import pretty_repr

from somesy.core.models import Entity, Person, ProjectMetadata, parse_name_email
from somesy.core.writer import ProjectMetadataWriter, format_toml_data

from .models import JuliaConfig

logger = logging.getLogger("somesy")


class Julia(ProjectMetadataWriter):
    """Julia config file handler parsed from Project.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: bool | None = False,
    ):
        """Julia config file handler parsed from Project.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        super().__init__(
            path,
            create_if_not_exists=False,
            pass_validation=pass_validation,
        )

    def _load(self) -> None:
        """Load Project.toml file."""
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
            f"Validating config using {JuliaConfig.__name__}: {pretty_repr(config)}"
        )
        JuliaConfig(**config)

    def save(self, path: Path | None = None) -> None:
        """Save the julia file."""
        path = path or self.path
        format_toml_data(self._data)

        with open(path, "w", encoding="utf-8") as f:
            tomlkit.dump(self._data, f)

    @staticmethod
    def _from_person(person: Person | Entity):
        """Convert project metadata person object to a name+email string."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person_obj: str) -> Person | Entity | None:
        """Convert from free string to person or entity object."""
        return parse_name_email(person_obj)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        # overridden to not sync fields that are not present in the Project.toml file
        if metadata.name is not None:
            self.name = metadata.name
        if metadata.version:
            self.version = metadata.version

        if metadata.authors():
            self._sync_authors(metadata)
