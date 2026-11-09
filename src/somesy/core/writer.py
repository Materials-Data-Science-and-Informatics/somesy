"""Project metadata writer base-class."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.items import AoT, Array, InlineTable

from somesy.core.models import (
    Entity,
    Person,
    ProjectMetadata,
    find_matching_person,
    is_blank_person,
)

logger = logging.getLogger("somesy")

# person fields that are role/contribution flags, not part of the person's identity
_UNMANAGED_PERSON_FIELDS = frozenset(
    {
        "author",
        "publication_author",
        "maintainer",
        "contribution",
        "contribution_types",
        "contribution_begin",
        "contribution_end",
    }
)


def toml_array(value: list) -> Array:
    """Build a multiline tomlkit array, with spaced inline tables."""
    array = tomlkit.array()
    array.extend(value)
    array.multiline(True)
    # Ensure whitespace after commas in inline tables
    for item in array:
        if isinstance(item, InlineTable):
            # Rebuild the inline table with desired formatting
            formatted_item = tomlkit.inline_table()
            for k, v in item.value.items():
                formatted_item[k] = v
            formatted_item.trivia.trail = " "  # Add space after each comma
            array[array.index(item)] = formatted_item
    return array


def multiline_description(table: Any) -> None:
    """Store a description containing line breaks as a multiline TOML string."""
    if "description" in table and "\n" in table["description"]:
        table["description"] = tomlkit.string(table["description"], multiline=True)


def format_toml_data(data: Any) -> None:
    """Prepare a tomlkit document for saving: multiline description, multiline arrays."""
    multiline_description(data)

    # Handle arrays with proper formatting (snapshot, since we assign while iterating)
    for key, value in list(data.items()):
        if isinstance(value, list) and not isinstance(value, AoT):
            data[key] = toml_array(value)
        else:
            data[key] = value


class IgnoreKey:
    """Special marker to be passed for dropping a key from serialization."""


FieldKeyMapping = dict[str, str | list[str] | IgnoreKey]
"""Type to be used for the dict passed as `direct_mappings`."""

DictLike = Any
"""Dict-like that supports getitem, setitem, delitem, etc.

NOTE: This should be probably turned into a proper protocol.
"""


def license_expression(licenses) -> str:
    """Convert one or more license identifiers to an SPDX expression."""
    return " OR ".join(
        str(license)
        for license in (licenses if isinstance(licenses, list) else [licenses])
    )


class ProjectMetadataWriter(ABC):
    """Base class for Project Metadata Output Wrapper.

    All supported output formats are implemented as subclasses.
    """

    def __init__(
        self,
        path: Path,
        *,
        create_if_not_exists: bool | None = False,
        direct_mappings: FieldKeyMapping | None = None,
        merge: bool | None = False,
        pass_validation: bool | None = False,
    ) -> None:
        """Initialize the Project Metadata Output Wrapper.

        Use the `direct_mappings` dict to define
        format-specific location for certain fields,
        if no additional processing is needed that
        requires a customized setter.

        Args:
            path: Path to target output file.
            create_if_not_exists: Create an empty file if not exists. Defaults to False.
            direct_mappings: Dict with direct mappings of keys between somesy and target
            merge: Merge the output file with an existing file. Defaults to False.
            pass_validation: Pass validation for all output files. Defaults to False.

        """
        self._data: DictLike = {}
        self.path = path if isinstance(path, Path) else Path(path)
        self.create_if_not_exists = create_if_not_exists
        self.direct_mappings = direct_mappings or {}
        self.merge = merge
        self.pass_validation = pass_validation
        if self.path.is_file():
            self._load()
            if not self.pass_validation:
                self._validate()
        else:
            if self.create_if_not_exists:
                self._init_new_file()  # in memory only, written by save()
            else:
                raise FileNotFoundError(f"The file {self.path} does not exist.")

    def _init_new_file(self) -> None:
        """Initialize the data of a new target file (in memory only).

        Override to initialize with minimal contents, if needed.
        Make sure to set `self._data` to match the contents.
        The file is only created on disk by `save()`.
        """
        self._data = {}

    @abstractmethod
    def _load(self):
        """Load the output file and validate it.

        Implement this method so that it loads the file `self.path`
        into the `self._data` dict.

        The file is guaranteed to exist.
        """

    @abstractmethod
    def _validate(self) -> None:
        """Validate the target file data.

        Implement this method so that it checks
        the validity of the metadata (relevant to somesy)
        in that file and raises exceptions on failure.
        """

    @abstractmethod
    def save(self, path: Path | None) -> None:
        """Save the output file to the given path.

        Implement this in a way that will carefully
        update the target file with new metadata
        without destroying its other contents or structure.
        """

    def _get_property(
        self,
        key: str | list[str] | IgnoreKey,
        *,
        remove: bool = False,
    ) -> Any:
        """Get a property from the data.

        Override this to e.g. rewrite the retrieved key
        (e.g. if everything relevant is in some subobject).

        Args:
            key: Name of the key or sequence of multiple keys to retrieve the value.
            remove: If True, will remove the retrieved value and clean up the dict.

        """
        if isinstance(key, IgnoreKey):
            return None
        key_path = [key] if isinstance(key, str) else key

        curr: Any = self._data
        seq = [curr]
        for k in key_path:
            curr = curr.get(k)
            seq.append(curr)
            if curr is None:
                return None

        if remove:
            seq.pop()
            del seq[-1][key_path[-1]]  # remove leaf value
            # clean up the tree
            for path_key, dct in reversed(
                list(zip(key_path[:-1], seq[:-1], strict=False))
            ):
                if not dct.get(path_key):
                    del dct[path_key]

        return curr

    def _set_property(self, key: str | list[str] | IgnoreKey, value: Any) -> None:
        """Set a property in the data.

        Note if there are lists along the path, they are cleared out.

        Override this to e.g. rewrite the retrieved key
        (e.g. if everything relevant is in some subobject).
        """
        if isinstance(key, IgnoreKey):
            return
        key_path = [key] if isinstance(key, str) else key

        if not value:  # remove value and clean up the sub-dict
            self._get_property(key_path, remove=True)
            return

        # create path on the fly if needed
        curr = self._data
        for path_key in key_path[:-1]:
            if path_key not in curr:
                curr[path_key] = {}
            curr = curr[path_key]

        curr[key_path[-1]] = value

    # ----
    # special handling for person metadata

    def _merge_person_metadata(
        self,
        old: Sequence[Person | Entity],
        new: Sequence[Person | Entity],
    ) -> list[Person | Entity]:
        """Update metadata of a list of persons.

        Will identify people based on orcid, email or full name.

        If old list has same person listed multiple times,
        the resulting list will too (we cannot correctly merge for external formats.)
        """
        new_people = []  # list for new people (e.g. added authors)
        # flag, meaning "person was not removed"
        still_exists = [False for i in range(len(old))]
        # copies of old person data, to be modified
        modified_people = [p.model_copy() for p in old]

        # try to match new people to existing old ones
        # (inefficient, but author list are not that long usually)
        for person_meta in new:
            person_update = person_meta.model_dump()
            index = find_matching_person(person_meta, modified_people)
            if index is not None:
                person = modified_people[index]

                # not new person (-> will not append new record)
                # still exists (-> will not be removed from list)
                still_exists[index] = True

                # the input is the source of truth for the managed fields:
                # fields missing in the input are removed from the output person
                # (unknown extra keys of the output are kept)
                fields = type(person).model_fields
                cleared = {
                    k: fields[k].get_default(call_default_factory=True)
                    for k in person.model_dump()
                    if k in fields
                    and k not in person_update
                    and k not in _UNMANAGED_PERSON_FIELDS
                }
                updated = person.model_copy(update={**person_update, **cleared})

                # if there were changes -> update person
                if updated.model_dump() != person.model_dump():
                    modified_people[index] = updated

                    # show effective update in debug log
                    old_fmt = self._from_person(person)
                    new_fmt = self._from_person(updated)
                    if old_fmt != new_fmt:
                        logger.debug(f"Updating person\n{old_fmt}\nto\n{new_fmt}")
            else:
                new_people.append(person_meta)

        # show added and removed people in debug log
        removed_people = [old[i] for i in range(len(old)) if not still_exists[i]]
        for person in removed_people:
            logger.debug(f"Removing person\n{self._from_person(person)}")
        for person in new_people:
            logger.debug(f"Adding person\n{self._from_person(person)}")

        # return updated list of (still existing) people,
        # and all new people coming after them.
        existing_modified = [
            modified_people[i] for i in range(len(old)) if still_exists[i]
        ]
        return existing_modified + new_people

    def _sync_person_list(
        self, old: list[Any], new: Sequence[Person | Entity]
    ) -> list[Any]:
        """Sync a list of persons with new metadata.

        Args:
            old (List[Any]): list of persons in format-specific representation
            new (List[Person]): list of persons in somesy representation

        Returns:
            List[Any]: updated list of persons in format-specific representation

        """
        old_people: list[Person | Entity] = self._parse_people(old)

        # check if people are unique
        def filter_unique(
            people: Sequence[Person | Entity],
        ) -> list[Person | Entity]:
            """Filter out duplicate people from a list."""
            if people is None or len(people) == 0:
                return []

            unique_people: list[Person | Entity] = []
            # use same_person method to check if people are unique
            for person in people:
                if not any(person.same_person(p) for p in unique_people):
                    unique_people.append(person)

            return unique_people

        old_people_unique = filter_unique(old_people)
        new_people_unique = filter_unique(new)

        return self._merge_person_metadata(old_people_unique, new_people_unique)

    def _unparseable_people(self, role: str) -> tuple[Any, list[Any]]:
        """Return mapped key and raw existing entries of `role` that can't be parsed.

        Empty list if the target has no list-valued slot for the role.
        """
        key = self._get_key(role)
        raw = self._get_property(key)
        if not isinstance(raw, list):
            return key, []

        def unparseable(entry: Any) -> bool:
            if entry is None or self._is_blank_person(entry):
                return False
            try:
                return self._to_person(entry) is None
            except (KeyError, TypeError, ValueError, AttributeError):
                return True

        return key, [e for e in raw if unparseable(e)]

    def _reattach_people(self, key: Any, raw_entries: list[Any]) -> None:
        """Append raw entries (kept untouched) to the list stored under `key`."""
        if not raw_entries:
            return
        current = self._get_property(key)
        if isinstance(current, dict):  # some formats collapse one-item lists
            current = [current]
        if isinstance(current, list):
            self._set_property(key, current + raw_entries)

    def _sync_authors(self, metadata: ProjectMetadata) -> None:
        """Sync output file authors with authors from metadata.

        This method is existing for the publication_author special case
        when synchronizing to CITATION.cff.
        """
        if self.authors is None or len(self.authors) == 0:
            self.authors = metadata.authors()
        else:
            self.authors = self._sync_person_list(self.authors, metadata.authors())

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        if metadata.name is not None:
            self.name = metadata.name
        if metadata.description is not None:
            self.description = metadata.description

        if metadata.version:
            self.version = metadata.version

        if metadata.keywords:
            self.keywords = metadata.keywords

        # existing entries we cannot parse are kept untouched in the target
        kept = {r: self._unparseable_people(r) for r in ("authors", "maintainers")}

        if metadata.authors():
            self._sync_authors(metadata)
        self.maintainers = self._sync_person_list(
            self.maintainers, metadata.maintainers()
        )

        for key, raw_entries in kept.values():
            self._reattach_people(key, raw_entries)

        if licenses := metadata.license:
            self.license = license_expression(licenses)

        # keep existing values in the target file if somesy has none
        if metadata.homepage:
            self.homepage = str(metadata.homepage)
        if metadata.repository:
            self.repository = str(metadata.repository)
        if metadata.documentation:
            self.documentation = str(metadata.documentation)

    def harvest_metadata(self) -> dict[str, Any]:
        """Return metadata read from this endpoint in Somesy model terms."""
        data: dict[str, Any] = {}
        for field in (
            "name",
            "version",
            "description",
            "license",
            "homepage",
            "repository",
            "documentation",
            "keywords",
        ):
            try:
                value = getattr(self, field)
            except (KeyError, TypeError):
                continue
            if value not in (None, [], ""):
                data[field] = value

        people: list[Person] = []
        entities: list[Entity] = []
        for role in ("authors", "maintainers", "contributors"):
            for person in self._parse_people(getattr(self, role) or []):
                updates = (
                    {"author": True, "publication_author": True}
                    if role == "authors"
                    else {}
                )
                updates.update({"maintainer": True} if role == "maintainers" else {})
                person = person.model_copy(update=updates)
                if isinstance(person, Entity):
                    entities.append(person)
                else:
                    people.append(person)

        if people:
            data["people"] = people
        if entities:
            data["entities"] = entities
        return data

    @staticmethod
    @abstractmethod
    def _from_person(person: Person | Entity) -> Any:
        """Convert a `Person` or `Entity` object into suitable target format."""

    @staticmethod
    @abstractmethod
    def _to_person(person_obj: Any) -> Person | Entity | None:
        """Convert an object representing a person into a `Person` or `Entity` object."""

    @staticmethod
    def _is_blank_person(person_obj: Any) -> bool:
        """Return whether an existing person entry is blank, i.e. counts as no person."""
        return is_blank_person(person_obj)

    @classmethod
    def _parse_people(cls, people: list[Any] | None) -> list[Person | Entity]:
        """Return a list of Persons and Entities parsed from list of format-specific people representations."""
        # remove None values
        return [
            person
            for p in people or []
            if p is not None and not cls._is_blank_person(p)
            if (person := cls._to_person(p)) is not None
        ]

    # ----
    # individual magic getters and setters

    def _get_key(self, key: str) -> str | list[str] | IgnoreKey:
        """Get a key itself."""
        return self.direct_mappings.get(key) or key

    @property
    def name(self):
        """Return the name of the project."""
        return self._get_property(self._get_key("name"))

    @name.setter
    def name(self, name: str) -> None:
        """Set the name of the project."""
        self._set_property(self._get_key("name"), name)

    @property
    def version(self) -> str | None:
        """Return the version of the project."""
        return self._get_property(self._get_key("version"))

    @version.setter
    def version(self, version: str | None) -> None:
        """Set the version of the project."""
        self._set_property(self._get_key("version"), version)

    @property
    def description(self) -> str | None:
        """Return the description of the project."""
        return self._get_property(self._get_key("description"))

    @description.setter
    def description(self, description: str) -> None:
        """Set the description of the project."""
        self._set_property(self._get_key("description"), description)

    @property
    def authors(self):
        """Return the authors of the project."""
        authors = self._get_property(self._get_key("authors"))
        if authors is None or len(authors) == 0:
            return []

        # only return authors that can be converted to Person
        authors_validated = [
            author
            for author in authors
            if not self._is_blank_person(author) and self._to_person(author) is not None
        ]
        return authors_validated

    @authors.setter
    def authors(self, authors: list[Person | Entity]) -> None:
        """Set the authors of the project."""
        authors = [self._from_person(c) for c in authors]
        self._set_property(self._get_key("authors"), authors)

    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        maintainers = self._get_property(self._get_key("maintainers"))
        if maintainers is None:
            return []

        # only return maintainers that can be converted to Person
        maintainers_validated = [
            maintainer
            for maintainer in maintainers
            if not self._is_blank_person(maintainer)
            and self._to_person(maintainer) is not None
        ]
        return maintainers_validated

    @maintainers.setter
    def maintainers(self, maintainers: list[Person | Entity]) -> None:
        """Set the maintainers of the project."""
        maintainers = [self._from_person(c) for c in maintainers]
        self._set_property(self._get_key("maintainers"), maintainers)

    @property
    def contributors(self):
        """Return the contributors of the project."""
        return self._get_property(self._get_key("contributors"))

    @contributors.setter
    def contributors(self, contributors: list[Person | Entity]) -> None:
        """Set the contributors of the project."""
        contributors = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contributors)

    @property
    def keywords(self) -> list[str] | None:
        """Return the keywords of the project."""
        return self._get_property(self._get_key("keywords"))

    @keywords.setter
    def keywords(self, keywords: list[str]) -> None:
        """Set the keywords of the project."""
        self._set_property(self._get_key("keywords"), keywords)

    @property
    def license(self) -> Any:
        """Return the license of the project."""
        return self._get_property(self._get_key("license"))

    @license.setter
    def license(self, license: Any) -> None:
        """Set the license of the project."""
        self._set_property(self._get_key("license"), license)

    @property
    def homepage(self) -> str | None:
        """Return the homepage url of the project."""
        return self._get_property(self._get_key("homepage"))

    @homepage.setter
    def homepage(self, value: str | None) -> None:
        """Set the homepage url of the project."""
        self._set_property(self._get_key("homepage"), value)

    @property
    def repository(self) -> str | dict | None:
        """Return the repository url of the project."""
        return self._get_property(self._get_key("repository"))

    @repository.setter
    def repository(self, value: str | dict | None) -> None:
        """Set the repository url of the project."""
        self._set_property(self._get_key("repository"), value)

    @property
    def documentation(self) -> str | dict | None:
        """Return the documentation url of the project."""
        return self._get_property(self._get_key("documentation"))

    @documentation.setter
    def documentation(self, value: str | dict | None) -> None:
        """Set the documentation url of the project."""
        self._set_property(self._get_key("documentation"), value)
