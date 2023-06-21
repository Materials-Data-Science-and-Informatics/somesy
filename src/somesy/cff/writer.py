"""Citation File Format (CFF) parser and saver."""
from json import loads
from pathlib import Path
from typing import List, Optional

from cffconvert.cli.create_citation import create_citation
from ruamel.yaml import YAML

from somesy.core.models import Person, ProjectMetadataWriter


class CFF(ProjectMetadataWriter):
    """Citation File Format (CFF) parser and saver."""

    def __init__(
        self,
        path: Path,
        create_if_not_exists: bool = True,
    ):
        """Citation File Format (CFF) parser.

        See [somesy.core.models.ProjectMetadataWriter.__init__][].
        """
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

        super().__init__(path, create_if_not_exists=create_if_not_exists)

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

    # ----
    # getters/setters performing the mapping

    @property
    def name(self) -> str:
        """Project name."""
        return self._get_property("title")

    @name.setter
    def name(self, name: str) -> None:
        """Set project name."""
        self._set_property("title", name)

    @property
    def description(self) -> Optional[str]:
        """Project description."""
        return self._get_property("abstract")

    @description.setter
    def description(self, description: str) -> None:
        """Set project description."""
        self._set_property("abstract", description)

    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        return self._get_property("contact")

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set the maintainers of the project."""
        maintainers = [self._from_person(c) for c in maintainers]
        self._set_property("contact", maintainers)

    @property
    def homepage(self) -> Optional[str]:
        """Project homepage url."""
        return self._get_property("url")

    @homepage.setter
    def homepage(self, homepage: Optional[str]) -> None:
        """Set project homepage url."""
        self._set_property("url", homepage)

    @property
    def repository(self) -> Optional[str]:
        """Project repository url."""
        return self._get_property("repository-code")

    @repository.setter
    def repository(self, repository: Optional[str]) -> None:
        """Set project repository url."""
        self._set_property("repository-code", repository)
