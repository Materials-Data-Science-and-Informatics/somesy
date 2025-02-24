"""Pyproject writers for setuptools and rust."""

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

from rich.pretty import pretty_repr
from tomlkit import dump, load, table

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, IgnoreKey, ProjectMetadataWriter

from .models import RustConfig, check_keyword

logger = logging.getLogger("somesy")


class Rust(ProjectMetadataWriter):
    """Rust config file handler parsed from Cargo.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: Optional[bool] = False,
    ):
        """Rust config file handler parsed from Cargo.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self._section = ["package"]
        mappings: FieldKeyMapping = {
            "maintainers": IgnoreKey(),
        }
        super().__init__(
            path,
            create_if_not_exists=False,
            direct_mappings=mappings,
            pass_validation=pass_validation,
        )

    def _load(self) -> None:
        """Load Cargo.toml file."""
        with open(self.path) as f:
            self._data = load(f)

    def _validate(self) -> None:
        """Validate rust config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        if self.pass_validation:
            return
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {RustConfig.__name__}: {pretty_repr(config)}"
        )
        RustConfig(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the Cargo.toml file."""
        path = path or self.path
        with open(path, "w") as f:
            dump(self._data, f)

    def _get_property(
        self, key: Union[str, List[str], IgnoreKey], *, remove: bool = False, **kwargs
    ) -> Optional[Any]:
        """Get a property from the Cargo.toml file."""
        if isinstance(key, IgnoreKey):
            return None
        key_path = [key] if isinstance(key, str) else key
        full_path = self._section + key_path
        return super()._get_property(full_path, remove=remove, **kwargs)

    def _set_property(self, key: Union[str, List[str], IgnoreKey], value: Any) -> None:
        """Set a property in the Cargo.toml file."""
        if isinstance(key, IgnoreKey):
            return
        key_path = [key] if isinstance(key, str) else key

        if not value:  # remove value and clean up the sub-dict
            self._get_property(key_path, remove=True)
            return

        # get the tomlkit object of the section
        dat = self._get_property([])

        # dig down, create missing nested objects on the fly
        curr = dat
        for key in key_path[:-1]:
            if key not in curr:
                curr.add(key, table())
            curr = curr[key]
        curr[key_path[-1]] = value

    @staticmethod
    def _from_person(person: Union[Person, Entity]):
        """Convert project metadata person object to rust string for person format "full name <email>."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person: str) -> Optional[Union[Person, Entity]]:
        """Parse rust person string to a Person. It has format "full name <email>." but email is optional.

        Since there is no way to know whether this entry is a person or an entity, we will directly convert to Person.
        """
        try:
            return Person.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.info(f"Cannot convert {person} to Person object, trying Entity.")

        try:
            return Entity.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person} to Entity.")
            return None

    @classmethod
    def _parse_people(cls, people: Optional[List[Any]]) -> List[Person]:
        """Return a list of Persons parsed from list of format-specific people representations. to_person can return None, so filter out None values."""
        return list(filter(None, map(cls._to_person, people or [])))

    @property
    def keywords(self) -> Optional[List[str]]:
        """Return the keywords of the project."""
        return self._get_property(self._get_key("keywords"))

    @keywords.setter
    def keywords(self, keywords: List[str]) -> None:
        """Set the keywords of the project."""
        validated_keywords = []
        for keyword in keywords:
            try:
                check_keyword(keyword)
                validated_keywords.append(keyword)
            except ValueError as e:
                logger.debug(f"Invalid keyword {keyword}: {e}")

        # keyword count should max 5, so delete the rest
        if len(validated_keywords) > 5:
            validated_keywords = validated_keywords[:5]
        self._set_property(self._get_key("keywords"), validated_keywords)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync the rust config with the project metadata."""
        super().sync(metadata)

        # if there is a license file, remove the license field
        if self._get_key("license_file"):
            self.license = None
