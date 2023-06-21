"""Citation File Format (CFF) parser and saver."""
from json import loads
from pathlib import Path
from typing import Optional

from cffconvert.cli.create_citation import create_citation
from ruamel.yaml import YAML

from somesy.core.models import Person
from somesy.core.writer import ProjectMetadataWriter


class CFF(ProjectMetadataWriter):
    """Citation File Format (CFF) parser and saver."""

    def __init__(
        self,
        path: Path,
        create_if_not_exists: bool = True,
    ):
        """Citation File Format (CFF) parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

        mappings = {
            "name": ["title"],
            "description": ["abstract"],
            "homepage": ["url"],
            "repository": ["repository-code"],
            "maintainers": ["contact"],
        }
        super().__init__(
            path, create_if_not_exists=create_if_not_exists, direct_mappings=mappings
        )

    def _init_new_file(self):
        """Initialize new CFF file."""
        self._data = {
            "cff-version": "1.2.0",
            "message": "If you use this software, please cite it using these metadata.",
            "type": "software",
            "title": "SOMESY_PLACEHOLDER",
            "authors": [],
        }
        with open(self.path, "w") as f:
            self._yaml.dump(self._data, f)

    def _load(self):
        """Load the CFF file."""
        with open(self.path) as f:
            self._data = self._yaml.load(f)

    def _validate(self):
        """Validate the CFF file."""
        try:
            citation = create_citation(self.path, None)
            citation.validate()
        except ValueError as e:
            raise ValueError(f"CITATION.cff file is not valid!\n{e}") from e

    def save(self, path: Optional[Path] = None) -> None:
        """Save the CFF object to a file."""
        path = path or self.path
        self._yaml.dump(self._data, path)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to cff dict for person format."""
        cff_dict = loads(
            person.json(
                by_alias=True,
                exclude_none=True,
                exclude={
                    "contribution",
                    "contribution_type",
                    "contribution_begin",
                    "contribution_end",
                },
                exclude_unset=True,
            )
        )
        return cff_dict
