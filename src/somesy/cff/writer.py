"""Citation File Format (CFF) parser and saver."""

import json
import logging
from copy import deepcopy
from io import StringIO
from pathlib import Path

from cffconvert import Citation
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from somesy.core.core import atomic_write
from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, IgnoreKey, ProjectMetadataWriter

logger = logging.getLogger("somesy")


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
        self._was_empty = True  # nothing to validate yet
        self._data = {
            "cff-version": "1.2.0",
            "message": "If you use this software, please cite it using these metadata.",
            "type": "software",
        }

    def _load(self):
        """Load the CFF file."""
        with open(self.path, encoding="utf-8") as f:
            self._data = self._yaml.load(f)
        self._was_empty = not self._data
        if self._was_empty:  # empty or comment-only file, treat like a new one
            self._init_new_file()

    def _validate(self) -> None:
        """Validate the CFF file."""
        if self.pass_validation or self._was_empty:
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
        abstract = self._data.get("abstract")
        if isinstance(abstract, str) and "\n" in abstract:
            self._data["abstract"] = LiteralScalarString(abstract)

        stream = StringIO()
        self._yaml.dump(self._data, stream)
        atomic_write(path, stream.getvalue())

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
    def _to_person(person_obj) -> Person | Entity | None:
        """Parse CFF Person to a somesy Person or entity.

        Entries lacking a required field are skipped with a warning.
        """
        # if the object has key name, it is an entity
        if "name" in person_obj:
            model: type[Person | Entity] = Entity
        else:
            model = Person
        model._aliases()
        required = {
            f.alias or k for k, f in model.model_fields.items() if f.is_required()
        }
        if missing := required - set(person_obj.keys()):
            logger.warning(
                f"Skipping incomplete CITATION.cff person/entity {dict(person_obj)}, "
                f"missing: {', '.join(sorted(missing))}"
            )
            return None
        ret = model.make_partial(person_obj)

        # construct (partial) Person while preserving key order from YAML
        ret.set_key_order(list(person_obj.keys()))
        return ret
