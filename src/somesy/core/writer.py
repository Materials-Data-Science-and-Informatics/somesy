"""Project metadata writer base-class."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from somesy.core.models import Person, ProjectMetadata

logger = logging.getLogger("somesy")


class IgnoreKey:
    """Special marker to be passed for dropping a key from serialization."""


FieldKeyMapping = Dict[str, Union[List[str], IgnoreKey]]
"""Type to be used for the dict passed as `direct_mappings`."""

DictLike = Any
"""Dict-like that supports getitem, setitem, delitem, etc.

NOTE: This should be probably turned into a proper protocol.
"""


class ProjectMetadataWriter(ABC):
    """Base class for Project Metadata Output Wrapper.

    All supported output formats are implemented as subclasses.
    """

    def __init__(
        self,
        path: Path,
        *,
        create_if_not_exists: Optional[bool] = False,
        direct_mappings: FieldKeyMapping = None,
    ) -> None:
        """Initialize the Project Metadata Output Wrapper.

        Use the `direct_mappings` dict to define
        format-specific location for certain fields,
        if no additional processing is needed that
        requires a customized setter.

        Args:
            path: Path to target output file.
            create_if_not_exists: Create an empty CFF file if not exists. Defaults to True.
            direct_mappings: Dict with direct mappings of keys between somesy and target

        """
        self._data: DictLike = {}
        self.path = path if isinstance(path, Path) else Path(path)
        self.create_if_not_exists = create_if_not_exists
        self.direct_mappings = direct_mappings or {}

        if self.path.is_file():
            self._load()
            self._validate()
        else:
            if self.create_if_not_exists:
                self._init_new_file()
                self._load()
            else:
                raise FileNotFoundError(f"The file {self.path} does not exist.")

    def _init_new_file(self) -> None:
        """Create an new suitable target file.

        Override to initialize file with minimal contents, if needed.
        Make sure to set `self._data` to match the contents.
        """
        self.path.touch()

    @abstractmethod
    def _load(self):
        """Load the output file and validate it.

        Implement this method so that it loads the file `self.path`
        into the `self._data` dict.

        The file is guaranteed to exist.
        """

    @abstractmethod
    def _validate(self):
        """Validate the target file data.

        Implement this method so that it checks
        the validity of the metadata (relevant to somesy)
        in that file and raises exceptions on failure.
        """

    @abstractmethod
    def save(self, path: Optional[Path]) -> None:
        """Save the output file to the given path.

        Implement this in a way that will carefully
        update the target file with new metadata
        without destroying its other contents or structure.
        """

    def _get_property(
        self,
        key: Union[str, List[str]],
        *,
        only_first: bool = False,
        remove: bool = False,
    ) -> Optional[Any]:
        """Get a property from the data.

        Override this to e.g. rewrite the retrieved key
        (e.g. if everything relevant is in some subobject).

        Args:
            key: Name of the key or sequence of multiple keys to retrieve the value.
            only_first: If True, returns only first entry if the value is a list.
            remove: If True, will remove the retrieved value and clean up the dict.

        """
        key_path = [key] if isinstance(key, str) else key

        curr = self._data
        seq = [curr]
        for k in key_path:
            curr = curr.get(k)
            curr = curr[0] if isinstance(curr, list) and only_first else curr
            seq.append(curr)
            if curr is None:
                return None

        if remove:
            seq.pop()
            del seq[-1][key_path[-1]]  # remove leaf value
            # clean up the tree
            for key, dct in reversed(list(zip(key_path[:-1], seq[:-1]))):
                if not dct.get(key):
                    del dct[key]

        if isinstance(curr, list) and only_first:
            return curr[0]
        return curr

    def _set_property(self, key: Union[str, List[str], IgnoreKey], value: Any) -> None:
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
        for key in key_path[:-1]:
            if key not in curr:
                curr[key] = {}
            curr = curr[key]

        curr[key_path[-1]] = value

    # ----
    # special handling for person metadata

    def _merge_person_metadata(
        self, old: List[Person], new: List[Person]
    ) -> List[Person]:
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
            person_existed = False
            for i in range(len(modified_people)):
                person = modified_people[i]
                if not person.same_person(person_meta):
                    continue

                # not new person (-> will not append new record)
                person_existed = True
                # still exists (-> will not be removed from list)
                still_exists[i] = True

                # if there were changes -> update person
                overlapping_fields = person.model_dump(
                    include=set(person_update.keys())
                )
                if person_update != overlapping_fields:
                    modified_people[i] = person.model_copy(update=person_update)

                    # show effective update in debug log
                    old_fmt = self._from_person(person)
                    new_fmt = self._from_person(modified_people[i])
                    if old_fmt != new_fmt:
                        logger.debug(f"Updating person\n{old_fmt}\nto\n{new_fmt}")

            if not person_existed:
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

    def _sync_person_list(self, old: List[Any], new: List[Person]) -> List[Any]:
        """Sync a list of persons with new metadata.

        Args:
            old (List[Any]): list of persons in format-specific representation
            new (List[Person]): list of persons in somesy representation

        Returns:
            List[Any]: updated list of persons in format-specific representation

        """
        old_people: List[Person] = self._parse_people(old)
        return self._merge_person_metadata(old_people, new)

    def _sync_authors(self, metadata: ProjectMetadata) -> None:
        """Sync output file authors with authors from metadata.

        This method is existing for the publication_author special case
        when synchronizing to CITATION.cff.
        """
        self.authors = self._sync_person_list(self.authors, metadata.authors())

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        self.name = metadata.name
        self.description = metadata.description

        if metadata.version:
            self.version = metadata.version

        if metadata.keywords:
            self.keywords = metadata.keywords

        self._sync_authors(metadata)
        self.maintainers = self._sync_person_list(
            self.maintainers, metadata.maintainers()
        )

        self.license = metadata.license.value

        self.homepage = str(metadata.homepage) if metadata.homepage else None
        self.repository = str(metadata.repository) if metadata.repository else None
        self.documentation = (
            str(metadata.documentation) if metadata.documentation else None
        )

    @staticmethod
    @abstractmethod
    def _from_person(person: Person) -> Any:
        """Convert a `Person` object into suitable target format."""

    @staticmethod
    @abstractmethod
    def _to_person(person_obj: Any) -> Person:
        """Convert an object representing a person into a `Person` object."""

    @classmethod
    def _parse_people(cls, people: Optional[List[Any]]) -> List[Person]:
        """Return a list of Persons parsed from list of format-specific people representations."""
        return list(map(cls._to_person, people or []))

    # ----
    # individual magic getters and setters

    def _get_key(self, key):
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
    def version(self) -> Optional[str]:
        """Return the version of the project."""
        return self._get_property(self._get_key("version"))

    @version.setter
    def version(self, version: str) -> None:
        """Set the version of the project."""
        self._set_property(self._get_key("version"), version)

    @property
    def description(self) -> Optional[str]:
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
        if authors is None:
            return []

        # only return authors that can be converted to Person
        authors_validated = [
            author for author in authors if self._to_person(author) is not None
        ]
        return authors_validated

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
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
            if self._to_person(maintainer) is not None
        ]
        return maintainers_validated

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set the maintainers of the project."""
        maintainers = [self._from_person(c) for c in maintainers]
        self._set_property(self._get_key("maintainers"), maintainers)

    @property
    def contributors(self):
        """Return the contributors of the project."""
        return self._get_property(self._get_key("contributors"))

    @contributors.setter
    def contributors(self, contributors: List[Person]) -> None:
        """Set the contributors of the project."""
        contributors = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contributors)

    @property
    def keywords(self) -> Optional[List[str]]:
        """Return the keywords of the project."""
        return self._get_property(self._get_key("keywords"))

    @keywords.setter
    def keywords(self, keywords: List[str]) -> None:
        """Set the keywords of the project."""
        self._set_property(self._get_key("keywords"), keywords)

    @property
    def license(self) -> Optional[str]:
        """Return the license of the project."""
        return self._get_property(self._get_key("license"))

    @license.setter
    def license(self, license: Optional[str]) -> None:
        """Set the license of the project."""
        self._set_property(self._get_key("license"), license)

    @property
    def homepage(self) -> Optional[str]:
        """Return the homepage url of the project."""
        return self._get_property(self._get_key("homepage"))

    @homepage.setter
    def homepage(self, value: Optional[str]) -> None:
        """Set the homepage url of the project."""
        self._set_property(self._get_key("homepage"), value)

    @property
    def repository(self) -> Optional[Union[str, dict]]:
        """Return the repository url of the project."""
        return self._get_property(self._get_key("repository"))

    @repository.setter
    def repository(self, value: Optional[Union[str, dict]]) -> None:
        """Set the repository url of the project."""
        self._set_property(self._get_key("repository"), value)

    @property
    def documentation(self) -> Optional[Union[str, dict]]:
        """Return the documentation url of the project."""
        return self._get_property(self._get_key("documentation"))

    @documentation.setter
    def documentation(self, value: Optional[Union[str, dict]]) -> None:
        """Set the documentation url of the project."""
        self._set_property(self._get_key("documentation"), value)
