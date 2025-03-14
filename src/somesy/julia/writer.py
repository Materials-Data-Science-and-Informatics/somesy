"""Julia writer."""

import logging
from pathlib import Path
from typing import Optional, Union

import tomlkit
from rich.pretty import pretty_repr

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import ProjectMetadataWriter

from .models import JuliaConfig

logger = logging.getLogger("somesy")


class Julia(ProjectMetadataWriter):
    """Julia config file handler parsed from Project.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: Optional[bool] = False,
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
            f"Validating config using {JuliaConfig.__name__}: {pretty_repr(config)}"
        )
        JuliaConfig(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the julia file."""
        path = path or self.path
        if "description" in self._data:
            if "\n" in self._data["description"]:
                self._data["description"] = tomlkit.string(
                    self._data["description"], multiline=True
                )

        # Handle arrays with proper formatting
        for key, value in self._data.items():
            if isinstance(value, list):
                array = tomlkit.array()
                array.extend(value)
                array.multiline(True)
                # Ensure whitespace after commas in inline tables
                for item in array:
                    if isinstance(item, tomlkit.items.InlineTable):
                        # Rebuild the inline table with desired formatting
                        formatted_item = tomlkit.inline_table()
                        for k, v in item.value.items():
                            formatted_item[k] = v
                        formatted_item.trivia.trail = " "  # Add space after each comma
                        array[array.index(item)] = formatted_item
                self._data[key] = array
            else:
                self._data[key] = value

        with open(path, "w") as f:
            tomlkit.dump(self._data, f)

    @staticmethod
    def _from_person(person: Union[Person, Entity]):
        """Convert project metadata person object to a name+email string."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person: str) -> Optional[Person]:
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
        # overridden to not sync fields that are not present in the Project.toml file
        self.name = metadata.name
        self.version = metadata.version

        self._sync_authors(metadata)
