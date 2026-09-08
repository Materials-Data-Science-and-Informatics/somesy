"""codemeta.json creation module."""

import json
import logging
import uuid
from collections import OrderedDict
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from somesy.codemeta.utils import validate_codemeta
from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, ProjectMetadataWriter

logger = logging.getLogger("somesy")

V2_CONTEXT = "https://doi.org/10.5063/schema/codemeta-2.0"
V3_CONTEXT = "https://w3id.org/codemeta/3.1"


class CodeMeta(ProjectMetadataWriter):
    """Codemeta.json parser and saver."""

    def __init__(
        self,
        path: Path,
        merge: bool | None = False,
        pass_validation: bool | None = False,
    ):
        """Codemeta.json parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self.merge = merge
        self._default_context = V3_CONTEXT
        mappings: FieldKeyMapping = {
            "repository": ["codeRepository"],
            "homepage": ["softwareHelp"],
            "documentation": ["buildInstructions"],
            "keywords": ["keywords"],
            "authors": ["author"],
            "maintainers": ["maintainer"],
            "contributors": ["contributor"],
        }
        super().__init__(
            path,
            create_if_not_exists=True,
            direct_mappings=mappings,
            merge=merge,
            pass_validation=pass_validation,
        )

    @property
    def authors(self):
        """Return the only author of the codemeta.json file as list."""
        return self._get_property(self._get_key("publication_authors")) or []

    @authors.setter
    def authors(self, authors: list[Person | Entity]) -> None:
        """Set the authors of the project."""
        authors_dict = self._people_with_roles(authors)
        self._set_property(self._get_key("authors"), authors_dict)

    @property
    def maintainers(self):
        """Return the maintainers of the codemeta.json file."""
        return self._get_property(self._get_key("maintainers"))

    @maintainers.setter
    def maintainers(self, maintainers: list[Person | Entity]) -> None:
        """Set the maintainers of the project."""
        maintainers_dict = [self._from_person(m) for m in maintainers]
        self._set_property(self._get_key("maintainers"), maintainers_dict)

    @property
    def contributors(self):
        """Return the contributors of the codemeta.json file."""
        return self._get_property(self._get_key("contributors"))

    @contributors.setter
    def contributors(self, contributors: list[Person | Entity]) -> None:
        """Set the contributors of the project."""
        contributors_dict = self._people_with_roles(contributors)
        self._set_property(self._get_key("contributors"), contributors_dict)

    def _load(self) -> None:
        """Load codemeta.json file."""
        with self.path.open() as f:
            self._data = json.load(f, object_pairs_hook=OrderedDict)

    def _upgrade_to_v3(self) -> None:
        """Normalize an existing CodeMeta file before v3.1 validation."""
        context = self._data.get("@context", [])
        context = context if isinstance(context, list) else [context]
        context = [item for item in context if item != V2_CONTEXT]
        if V3_CONTEXT not in context:
            context.insert(0, V3_CONTEXT)
        self._data["@context"] = context

        for old, new in (
            ("contIntegration", "continuousIntegration"),
            ("embargoDate", "embargoEndDate"),
        ):
            if old in self._data and new not in self._data:
                self._data[new] = self._data[old]
            self._data.pop(old, None)

    def _validate(self) -> None:
        """Validate codemeta.json content using pydantic class."""
        if self.pass_validation:
            return
        loaded_data = self._data
        if self.merge:
            self._data = deepcopy(self._data)
            self._upgrade_to_v3()
        try:
            invalid_fields = validate_codemeta(self._data)
        finally:
            self._data = loaded_data
        if invalid_fields and self.merge:
            raise ValueError(
                f"Invalid fields in codemeta.json: {invalid_fields}. Cannot merge with invalid fields."
            )

    def _init_new_file(self) -> None:
        """Create a new codemeta.json file with bare minimum generic data."""
        data = self._new_data()
        # dump to file
        with self.path.open("w+", newline="\n") as f:
            json.dump(data, f)

    def _new_data(self) -> dict[str, Any]:
        """Return the bare minimum generic CodeMeta data."""
        return {
            "@context": self._default_context,
            "@type": "SoftwareSourceCode",
            "author": [],
        }

    def save(self, path: Path | None = None) -> None:
        """Save the codemeta.json file."""
        path = path or self.path
        logger.debug(f"Saving codemeta.json to {path}")

        # copy the _data
        data = self._data.copy()

        # set license
        if "license" in data:
            licenses = data["license"]
            licenses = licenses if isinstance(licenses, list) else [licenses]
            data["license"] = [
                license
                if license.startswith("https://spdx.org/licenses/")
                else f"https://spdx.org/licenses/{license}"
                for license in licenses
            ]

        # if softwareHelp is set, set url to softwareHelp
        if "softwareHelp" in data:
            data["url"] = data["softwareHelp"]

        with path.open("w", newline="\n") as f:
            # codemeta.json indentation is 2 spaces
            json.dump(data, f)

    @staticmethod
    def _from_person(person: Person | Entity) -> dict:
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
    def _role_identifier(person: Person | Entity, person_dict: dict) -> str:
        """Return an identifier that can link a CodeMeta role to its person."""
        if identifier := person_dict.get("@id"):
            return identifier
        identity = person.email or person.full_name
        return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, f'{type(person).__name__}:{identity}')}"

    @staticmethod
    def _has_contribution_metadata(person: Person | Entity) -> bool:
        """Return whether a person has metadata representable by a CodeMeta role."""
        return any(
            (
                person.contribution,
                person.contribution_types,
                person.contribution_begin,
                person.contribution_end,
            )
        )

    def _people_with_roles(self, people: Sequence[Person | Entity]) -> list[dict]:
        """Serialize people and their granular contribution roles."""
        result = []
        for person in people:
            person_dict = self._from_person(person)
            if not self._has_contribution_metadata(person):
                result.append(person_dict)
                continue

            identifier = self._role_identifier(person, person_dict)
            person_dict["@id"] = identifier
            result.append(person_dict)

            role_names: list[str | None] = []
            if person.contribution:
                role_names.append(person.contribution)
            role_names.extend(
                contribution_type.value
                for contribution_type in person.contribution_types or []
            )
            if not role_names:
                role_names.append(None)
            for role_name in role_names:
                role = {"@type": "Role", "schema:author": identifier}
                if role_name:
                    role["roleName"] = role_name
                if person.contribution_begin:
                    role["startDate"] = person.contribution_begin.isoformat()
                if person.contribution_end:
                    role["endDate"] = person.contribution_end.isoformat()
                result.append(role)
        return result

    @staticmethod
    def _to_person(person_obj) -> Person | Entity:
        """Convert codemeta.json dict or str for person/entity format to project metadata person object."""
        if "name" in person_obj:
            entity_obj = {"name": person_obj["name"]}
            return Entity(**entity_obj)
        else:
            person_data = {}
            if "givenName" in person_obj:
                person_data["given_names"] = person_obj["givenName"].strip()
            if "familyName" in person_obj:
                person_data["family_names"] = person_obj["familyName"].strip()
            if "email" in person_obj:
                person_data["email"] = person_obj["email"].strip()
            if "@id" in person_obj:
                person_data["orcid"] = person_obj["@id"].strip()
            if "address" in person_obj:
                person_data["address"] = person_obj["address"].strip()

            return Person(**person_data)

    def _sync_person_list(
        self, old: list[Any], new: Sequence[Person | Entity]
    ) -> list[Any]:
        """Override the _sync_person_list function from ProjectMetadataWriter.

        This method wont care about existing persons in codemeta.json file.

        Args:
            old (List[Any]): existing persons in codemeta.json file, in this case ignored in the output. However, it is necessary to make the function compatible with the parent class.
            new (List[Person]): new persons to add to codemeta.json file

        Returns:
            List[Any]: list of new persons to add to codemeta.json file

        """
        return list(new)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync codemeta.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        if not self.merge:
            self._data = self._new_data()
        else:
            self._upgrade_to_v3()
            self._data["@type"] = "SoftwareSourceCode"
            if metadata.authors():
                self._data["author"] = []
            self._data["maintainer"] = []
            self._data["contributor"] = []

        super().sync(metadata)
        if metadata.doi:
            self._data["identifier"] = f"https://doi.org/{metadata.doi}"
        if licenses := metadata.license:
            self.license = [
                f"https://spdx.org/licenses/{license.value}"
                for license in (licenses if isinstance(licenses, list) else [licenses])
            ]
        self.contributors = metadata.contributors()

        if "softwareHelp" in self._data:
            self._data["url"] = self._data["softwareHelp"]
