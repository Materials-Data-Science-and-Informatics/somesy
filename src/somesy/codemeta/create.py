"""codemeta.json creation module."""
import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional

from rich.pretty import pretty_repr

from somesy.core.models import Person, ProjectMetadata
from somesy.core.writer import ProjectMetadataWriter

logger = logging.getLogger("somesy")


class Codemeta(ProjectMetadataWriter):
    """Codemeta.json parser and saver."""

    def __init__(
        self,
        path: Path,
    ):
        """Codemeta.json parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        mappings = {
            "repository": ["codeRepository"],
            "homepage": ["softwareHelp"],
            "keywords": ["keywords"],
            "authors": ["author"],
            "maintainers": ["maintainer"],
            "contributors": ["contributor"],
        }
        super().__init__(path, create_if_not_exists=True, direct_mappings=mappings)

    @property
    def authors(self):
        """Return the only author of the package.json file as list."""
        return self._get_property(self._get_key("publication_authors")) or []

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set the authors of the project."""
        authors = [self._from_person(a) for a in authors]
        self._set_property(self._get_key("authors"), authors)

    @property
    def contributors(self):
        """Return the contributors of the package.json file."""
        return self._get_property(self._get_key("contributors"))

    @contributors.setter
    def contributors(self, contributors: List[Person]) -> None:
        """Set the contributors of the project."""
        contributors = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contributors)

    def _load(self) -> None:
        """Load package.json file."""
        with self.path.open() as f:
            self._data = json.load(f, object_pairs_hook=OrderedDict)

    def _validate(self) -> None:
        """Validate package.json content using pydantic class."""
        config = dict(self._get_property([]))

        logger.debug(
            f"No validation for codemeta {Codemeta.__name__}: {pretty_repr(config)}"
        )

    def _init_new_file(self) -> None:
        data = {
            "@context": [
                "https://doi.org/10.5063/schema/codemeta-2.0",
                "https://w3id.org/software-iodata",
                "https://raw.githubusercontent.com/jantman/repostatus.org/master/badges/latest/ontology.jsonld",
                "https://schema.org",
                "https://w3id.org/software-types",
            ],
            "@type": "SoftwareSourceCode",
            "author": [],
        }
        # dump to file
        with self.path.open("w") as f:
            json.dump(data, f, indent=2)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the package.json file."""
        path = path or self.path
        logger.debug(f"Saving package.json to {path}")

        # copy the _data
        data = self._data.copy()

        # set license
        if "license" in data:
            data["license"] = (f"https://spdx.org/licenses/{data['license']}",)

        # if softwareHelp is set, set url to softwareHelp
        if "softwareHelp" in data:
            data["url"] = data["softwareHelp"]

        with path.open("w") as f:
            # package.json indentation is 2 spaces
            json.dump(data, f, indent=2)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to package.json dict for person format."""
        person_dict = {
            "givenName": person.given_names,
            "familyName": person.family_names,
            "@type": "Person",
        }
        if person.email:
            person_dict["email"] = person.email
        if person.orcid:
            person_dict["@id"] = str(person.orcid)
        return person_dict

    @staticmethod
    def _to_person(person) -> Person:
        """Convert package.json dict or str for person format to project metadata person object."""
        person_obj = {
            "given-names": person["givenName"],
            "family-names": person["familyName"],
        }
        if "email" in person:
            person_obj["email"] = person["email"].strip()
        if "@id" in person:
            person_obj["orcid"] = person["@id"].strip()
        return Person(**person_obj)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync package.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        super().sync(metadata)
        self.contributors = self._sync_person_list(self.contributors, metadata.people)
