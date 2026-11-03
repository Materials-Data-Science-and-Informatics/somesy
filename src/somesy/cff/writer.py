"""Citation File Format (CFF) parser and saver."""

import json
from copy import deepcopy
from io import StringIO
from pathlib import Path

from cffconvert import Citation
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, IgnoreKey, ProjectMetadataWriter


def _drop_rorid(data) -> None:
    """Remove `rorid` from entities; earlier somesy versions wrote this non-CFF key."""
    for key in ("authors", "contact"):
        for entry in data.get(key) or []:
            if isinstance(entry, dict) and "name" in entry:
                entry.pop("rorid", None)


class CFF(ProjectMetadataWriter):
    """Citation File Format (CFF) parser and saver."""

    def __init__(
        self,
        path: Path,
        create_if_not_exists: bool = True,
        pass_validation: bool = False,
    ):
        """Citation File Format (CFF) parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self._yaml.width = 120

        mappings: FieldKeyMapping = {
            "name": ["title"],
            "description": ["abstract"],
            "homepage": ["url"],
            "repository": ["repository-code"],
            "documentation": IgnoreKey(),
            "maintainers": ["contact"],
        }
        super().__init__(
            path,
            create_if_not_exists=create_if_not_exists,
            direct_mappings=mappings,
            pass_validation=pass_validation,
        )

    def _init_new_file(self):
        """Initialize new CFF file."""
        self._data = {
            "cff-version": "1.2.0",
            "message": "If you use this software, please cite it using these metadata.",
            "type": "software",
        }
        with open(self.path, "w", encoding="utf-8") as f:
            self._yaml.dump(self._data, f)

    def _load(self):
        """Load the CFF file."""
        with open(self.path, encoding="utf-8") as f:
            self._data = self._yaml.load(f)

    def _validate(self) -> None:
        """Validate the CFF file."""
        if self.pass_validation:
            return
        try:
            # validate the loaded data without a stray `rorid` (repaired on sync)
            data = deepcopy(self._data)
            _drop_rorid(data)
            stream = StringIO()
            self._yaml.dump(data, stream)
            Citation(stream.getvalue(), src=self.path).validate()
        except ValueError as e:
            raise ValueError(f"CITATION.cff file is not valid!\n{e}") from e

    def save(self, path: Path | None = None) -> None:
        """Save the CFF object to a file."""
        path = path or self.path

        # if description have new line characters, it should be saved as multiline string
        if "abstract" in self._data and "\n" in self._data["abstract"]:
            self._data["abstract"] = LiteralScalarString(self._data["abstract"])

        self._yaml.dump(self._data, path)

    def _sync_authors(self, metadata: ProjectMetadata) -> None:
        """Ensure that publication authors are added all into author list."""
        self.authors = self._sync_person_list(
            self.authors, metadata.publication_authors()
        )

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync CFF metadata."""
        _drop_rorid(self._data)
        super().sync(metadata)
        # CFF 1.2.0 allows a list of SPDX ids
        if isinstance(metadata.license, list) and len(metadata.license) > 1:
            self.license = [license.value for license in metadata.license]
        # an abstract can be longer than a package summary, so prefer it here
        if metadata.abstract:
            self.description = metadata.abstract
        if metadata.doi:
            self._data["doi"] = metadata.doi

    @staticmethod
    def _from_person(person: Person | Entity):
        """Convert project metadata person or entity object to cff dict for person format."""
        json_str = person.model_dump_json(
            exclude={
                "contribution",
                "contribution_types",
                "contribution_begin",
                "contribution_end",
                "author",
                "publication_author",
                "maintainer",
            },
            by_alias=True,  # e.g. family_names -> family-names, etc.
        )
        ret = json.loads(json_str)
        ret.pop("rorid", None)  # not a CFF field
        return ret

    @staticmethod
    def _to_person(person_obj) -> Person | Entity:
        """Parse CFF Person to a somesy Person or entity."""
        # if the object has key name, it is an entity
        if "name" in person_obj:
            Entity._aliases()
            ret = Entity.make_partial(person_obj)
        else:
            Person._aliases()
            ret = Person.make_partial(person_obj)

        # construct (partial) Person while preserving key order from YAML
        ret.set_key_order(list(person_obj.keys()))
        return ret
