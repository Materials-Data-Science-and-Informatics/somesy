"""codemeta.json creation module."""

import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, List, Optional

from rich.pretty import pretty_repr

from somesy.core.models import Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, ProjectMetadataWriter
from somesy.json_wrapper import json

logger = logging.getLogger("somesy")


class CodeMeta(ProjectMetadataWriter):
    """Codemeta.json parser and saver."""

    def __init__(
        self,
        path: Path,
    ):
        """Codemeta.json parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        mappings: FieldKeyMapping = {
            "repository": ["codeRepository"],
            "homepage": ["softwareHelp"],
            "documentation": ["buildInstructions"],
            "keywords": ["keywords"],
            "authors": ["author"],
            "maintainers": ["maintainer"],
            "contributors": ["contributor"],
        }
        # delete the file if it exists
        if path.is_file():
            logger.verbose("Deleting existing codemeta.json file.")
            path.unlink()
        super().__init__(path, create_if_not_exists=True, direct_mappings=mappings)

    @property
    def authors(self):
        """Return the only author of the codemeta.json file as list."""
        return self._get_property(self._get_key("publication_authors")) or []

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set the authors of the project."""
        authors = [self._from_person(a) for a in authors]
        self._set_property(self._get_key("authors"), authors)

    @property
    def contributors(self):
        """Return the contributors of the codemeta.json file."""
        return self._get_property(self._get_key("contributors"))

    @contributors.setter
    def contributors(self, contributors: List[Person]) -> None:
        """Set the contributors of the project."""
        contributors = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contributors)

    def _load(self) -> None:
        """Load codemeta.json file."""
        with self.path.open() as f:
            self._data = json.load(f, object_pairs_hook=OrderedDict)

    def _validate(self) -> None:
        """Validate codemeta.json content using pydantic class."""
        config = dict(self._get_property([]))

        logger.debug(
            f"No validation for codemeta.json files {CodeMeta.__name__}: {pretty_repr(config)}"
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
        with self.path.open("w+") as f:
            json.dump(data, f)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the codemeta.json file."""
        path = path or self.path
        logger.debug(f"Saving codemeta.json to {path}")

        # copy the _data
        data = self._data.copy()

        # set license
        if "license" in data:
            data["license"] = (f"https://spdx.org/licenses/{data['license']}",)

        # if softwareHelp is set, set url to softwareHelp
        if "softwareHelp" in data:
            data["url"] = data["softwareHelp"]

        with path.open("w") as f:
            # codemeta.json indentation is 2 spaces
            json.dump(data, f)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to codemeta.json dict for person format."""
        person_dict = {
            "@type": "Person",
        }
        if person.given_names:
            person_dict["givenName"] = person.given_names
        if person.family_names:
            person_dict["familyName"] = person.family_names
        if person.email:
            person_dict["email"] = person.email
        if person.orcid:
            person_dict["@id"] = str(person.orcid)
        if person.address:
            person_dict["address"] = person.address
        if person.affiliation:
            person_dict["affiliation"] = person.affiliation
        return person_dict

    @staticmethod
    def _to_person(person) -> Person:
        """Convert codemeta.json dict or str for person format to project metadata person object."""
        person_obj = {}
        if "givenName" in person:
            person_obj["given_names"] = person["givenName"].strip()
        if "familyName" in person:
            person_obj["family_names"] = person["familyName"].strip()
        if "email" in person:
            person_obj["email"] = person["email"].strip()
        if "@id" in person:
            person_obj["orcid"] = person["@id"].strip()
        if "address" in person:
            person_obj["address"] = person["address"].strip()

        return Person(**person_obj)

    def _sync_person_list(self, old: List[Any], new: List[Person]) -> List[Any]:
        """Override the _sync_person_list function from ProjectMetadataWriter.

        This method wont care about existing persons in codemeta.json file.

        Args:
            old (List[Any]): _description_
            new (List[Person]): _description_

        Returns:
            List[Any]: _description_

        """
        return new

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync codemeta.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        super().sync(metadata)
        self.contributors = self._sync_person_list(
            self.contributors, metadata.contributors()
        )
