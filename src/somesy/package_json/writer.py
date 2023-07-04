"""package.json parser and saver."""
import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from rich.pretty import pretty_repr

from somesy.core.models import Person
from somesy.core.writer import ProjectMetadataWriter
from somesy.package_json.models import PackageJsonConfig

logger = logging.getLogger("somesy")


class PackageJSON(ProjectMetadataWriter):
    """package.json parser and saver."""

    def __init__(
        self,
        path: Path,
        create_if_not_exists: bool = False,
    ):
        """package.json parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        mappings = {
            "authors": ["author"],
        }
        super().__init__(
            path, create_if_not_exists=create_if_not_exists, direct_mappings=mappings
        )

    def _load(self) -> None:
        """Load package.json file."""
        with self.path.open() as f:
            self._data = json.load(f, object_pairs_hook=OrderedDict)

    def _validate(self) -> None:
        """Validate package.json content using pydantic class."""
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {PackageJsonConfig.__name__}: {pretty_repr(config)}"
        )
        PackageJsonConfig(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the CFF object to a file."""
        path = path or self.path

        with path.open("w") as f:
            # package.json indentation is 2 spaces
            json.dump(self._data, f, indent=2)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to package.json dict for person format."""
        person_dict = {"name": person.full_name}
        if person.email:
            person_dict["email"] = person.email
        if person.orcid:
            person_dict["url"] = person.orcid
        return person_dict

    @staticmethod
    def _to_person(person_obj: dict) -> Person:
        """Convert package.json dict for person format to project metadata person object."""
        names = list(map(lambda s: s.strip(), person_obj["name"].split()))
        return Person(
            **{
                "given-names": " ".join(names[:-1]),
                "family-names": names[-1],
                "email": person_obj["email"].strip(),
                "orcid": person_obj["url"].strip(),
            }
        )
