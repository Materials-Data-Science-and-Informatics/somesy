"""codemeta.json creation module."""

import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, List, Optional, Union

from somesy.codemeta.utils import validate_codemeta
from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, ProjectMetadataWriter

logger = logging.getLogger("somesy")


class CodeMeta(ProjectMetadataWriter):
    """Codemeta.json parser and saver."""

    def __init__(
        self,
        path: Path,
        merge: Optional[bool] = False,
        pass_validation: Optional[bool] = False,
    ):
        """Codemeta.json parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self.merge = merge
        self._default_context = [
            "https://doi.org/10.5063/schema/codemeta-2.0",
            "https://w3id.org/software-iodata",
            "https://raw.githubusercontent.com/jantman/repostatus.org/master/badges/latest/ontology.jsonld",
            "https://schema.org",
            "https://w3id.org/software-types",
        ]
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
        if path.is_file() and not self.merge:
            logger.verbose("Deleting existing codemeta.json file.")
            path.unlink()
        super().__init__(
            path,
            create_if_not_exists=True,
            direct_mappings=mappings,
            pass_validation=pass_validation,
        )

        # if merge is True, add necessary keys to the codemeta.json file
        if self.merge:
            # check if the context exists but is not a list
            if isinstance(self._data["@context"], str):
                self._data["@context"] = [self._data["@context"]]
            # finally add each item in the context to the codemeta.json file if it does not exist in the list
            for item in self._default_context:
                if item not in self._data["@context"]:
                    self._data["@context"].append(item)

            # add (or overwrite) the type
            self._data["@type"] = "SoftwareSourceCode"

            # overwrite authors, maintainers, contributors
            self._data["author"] = []
            self._data["maintainer"] = []
            self._data["contributor"] = []

    @property
    def authors(self):
        """Return the only author of the codemeta.json file as list."""
        return self._get_property(self._get_key("publication_authors")) or []

    @authors.setter
    def authors(self, authors: List[Union[Person, Entity]]) -> None:
        """Set the authors of the project."""
        authors_dict = [self._from_person(a) for a in authors]
        self._set_property(self._get_key("authors"), authors_dict)

    @property
    def contributors(self):
        """Return the contributors of the codemeta.json file."""
        return self._get_property(self._get_key("contributors"))

    @contributors.setter
    def contributors(self, contributors: List[Union[Person, Entity]]) -> None:
        """Set the contributors of the project."""
        contributors_dict = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contributors_dict)

    def _load(self) -> None:
        """Load codemeta.json file."""
        with self.path.open() as f:
            self._data = json.load(f, object_pairs_hook=OrderedDict)

    def _validate(self) -> None:
        """Validate codemeta.json content using pydantic class."""
        if self.pass_validation:
            return
        invalid_fields = validate_codemeta(self._data)
        if invalid_fields and self.merge:
            raise ValueError(
                f"Invalid fields in codemeta.json: {invalid_fields}. Cannot merge with invalid fields."
            )

    def _init_new_file(self) -> None:
        """Create a new codemeta.json file with bare minimum generic data."""
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
    def _from_person(person: Union[Person, Entity]) -> dict:
        """Convert project metadata person object to codemeta.json dict for person format."""
        if isinstance(person, Person):
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
                person_dict["identifier"] = str(person.orcid)
            if person.address:
                person_dict["address"] = person.address
            if person.affiliation:
                person_dict["affiliation"] = person.affiliation
            return person_dict
        else:
            entity_dict = {"@type": "Organization", "name": person.name}
            if person.address:
                entity_dict["address"] = person.address
            if person.email:
                entity_dict["email"] = person.email
            if person.date_start:
                entity_dict["startDate"] = person.date_start.isoformat()
            if person.date_end:
                entity_dict["endDate"] = person.date_end.isoformat()
            if person.website:
                entity_dict["@id"] = str(person.website)
                entity_dict["identifier"] = str(person.website)
            if person.rorid:
                entity_dict["@id"] = str(person.rorid)
                entity_dict["identifier"] = str(person.rorid)
            return entity_dict

    @staticmethod
    def _to_person(person) -> Union[Person, Entity]:
        """Convert codemeta.json dict or str for person/entity format to project metadata person object."""
        if "name" in person:
            entity_obj = {"name": person["name"]}
            return Entity(**entity_obj)
        else:
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

    def _sync_person_list(
        self, old: List[Any], new: List[Union[Person, Entity]]
    ) -> List[Any]:
        """Override the _sync_person_list function from ProjectMetadataWriter.

        This method wont care about existing persons in codemeta.json file.

        Args:
            old (List[Any]): existing persons in codemeta.json file, in this case ignored in the output. However, it is necessary to make the function compatible with the parent class.
            new (List[Person]): new persons to add to codemeta.json file

        Returns:
            List[Any]: list of new persons to add to codemeta.json file

        """
        return new

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync codemeta.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        super().sync(metadata)
        self.contributors = metadata.contributors()

        # add the default context items if they are not already in the codemeta.json file
        for item in self._default_context:
            if item not in self._data["@context"]:
                self._data["@context"].append(item)
