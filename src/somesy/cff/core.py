"""Citation File Format (CFF) parser and saver."""
from pathlib import Path
from typing import List, Optional

from ruamel.yaml import YAML

from somesy.cff.utils import person_to_cff_dict
from somesy.cff.validate import validate_citation
from somesy.core.models import Person, ProjectMetadataWriter


class CFF(ProjectMetadataWriter):
    """Citation File Format (CFF) parser and saver."""

    def __init__(
        self,
        path: Path,
        create_if_not_exists: bool = True,
    ):
        """Citation File Format (CFF) parser.

        Args:
            path (Path): File path to the CFF file.
            create_if_not_exists (bool, optional): Create an empty CFF file if not exists. Defaults to True.
        """
        self.path = path
        self.create_if_not_exists = create_if_not_exists
        self._yaml = YAML()

        # load and validate the CFF file
        self._load()
        self._validate()

    def _load(self):
        """Load the CFF file."""
        if not self.path.exists():
            if self.create_if_not_exists:
                self._create_empty_file()
                self._data = {}
                self._data["cff-version"] = "1.2.0"
                self._data[
                    "message"
                ] = "If you use this software, please cite it using these metadata."
                self._data["type"] = "software"
                self._data["title"] = "placeholder"
                self._data["authors"] = [{"given-names": "placeholder"}]
                with open(self.path, "w") as f:
                    self._yaml.dump(self._data, f)
            else:
                raise FileNotFoundError(f"CFF file {self.path} not found")
        else:
            with open(self.path) as f:
                self._data = self._yaml.load(f)

    def _validate(self):
        """Validate the CFF file."""
        validate_citation(self.path)

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
    def authors(self) -> List[str]:
        """Project authors."""
        return self._get_property("authors")

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set project authors."""
        self._set_property(
            "authors", [person_to_cff_dict(author) for author in authors]
        )

    @property
    def maintainers(self) -> Optional[List[str]]:
        """Project maintainers."""
        return self._get_property("contact")

    @maintainers.setter
    def maintainers(self, maintainers: Optional[List[Person]] = None) -> None:
        """Set project maintainers."""
        if maintainers is None:
            return
        self._set_property(
            "contact", [person_to_cff_dict(maintainer) for maintainer in maintainers]
        )

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

    def save(self, path: Optional[Path] = None) -> None:
        """Save the CFF object to a file."""
        if path:
            self._yaml.dump(self._data, path)
        else:
            self._yaml.dump(self._data, self.path)
