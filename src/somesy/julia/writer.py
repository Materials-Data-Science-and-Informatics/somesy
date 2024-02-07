"""Julia writer."""
import logging
import re
from pathlib import Path
from typing import Optional

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
        """Convert project metadata person object to poetry string for person format "full name <email>."""
        return f"{person.full_name} <{person.email}>"

    @staticmethod
    def _to_person(person_obj: str) -> Person:
        """Parse poetry person string to a Person."""
        m = re.match(r"\s*([^<]+)<([^>]+)>", person_obj)
        names, mail = (
            list(map(lambda s: s.strip(), m.group(1).split())),
            m.group(2).strip(),
        )
        # NOTE: for our purposes, does not matter what are given or family names,
        # we only compare on full_name anyway.
        return Person(
            **{
                "given-names": " ".join(names[:-1]),
                "family-names": names[-1],
                "email": mail,
            }
        )

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        self.name = metadata.name

        if metadata.version:
            self.version = metadata.version

        self._sync_authors(metadata)
