"""Cargo.toml writer for Rust projects."""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rich.pretty import pretty_repr
from tomlkit import dump, load, string, table

from somesy.core.models import Entity, Person, ProjectMetadata, parse_name_email
from somesy.core.writer import (
    FieldKeyMapping,
    IgnoreKey,
    ProjectMetadataWriter,
    toml_array,
)

from .models import RustConfig, check_keyword

logger = logging.getLogger("somesy")


class Rust(ProjectMetadataWriter):
    """Rust config file handler parsed from Cargo.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: bool | None = False,
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
        with open(self.path, encoding="utf-8") as f:
            self._data = load(f)

    def _validate(self) -> None:
        """Validate rust config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {RustConfig.__name__}: {pretty_repr(config)}"
        )
        RustConfig(**config)

    def save(self, path: Path | None = None) -> None:
        """Save the Cargo.toml file."""
        path = path or self.path

        if (
            "description" in self._data["package"]
            and "\n" in self._data["package"]["description"]
        ):
            self._data["package"]["description"] = string(
                self._data["package"]["description"], multiline=True
            )

        with open(path, "w", encoding="utf-8") as f:
            dump(self._data, f)

    def _get_property(
        self, key: str | list[str] | IgnoreKey, *, remove: bool = False, **kwargs
    ) -> Any:
        """Get a property from the Cargo.toml file."""
        if isinstance(key, IgnoreKey):
            return None
        key_path = [key] if isinstance(key, str) else key
        full_path = self._section + key_path
        value = super()._get_property(full_path, remove=remove, **kwargs)
        if not remove and self._is_workspace_ref(value):
            return None  # inherited from the workspace, treat as absent
        return value

    @staticmethod
    def _is_workspace_ref(value: Any) -> bool:
        """Check whether value is a workspace inheritance table `{workspace = true}`."""
        return isinstance(value, Mapping) and value.get("workspace") is True

    def _set_property(self, key: str | list[str] | IgnoreKey, value: Any) -> None:
        """Set a property in the Cargo.toml file."""
        if isinstance(key, IgnoreKey):
            return
        key_path = [key] if isinstance(key, str) else key

        # keep workspace inheritance, e.g. `version.workspace = true`
        existing = super()._get_property(self._section + key_path)
        if self._is_workspace_ref(existing):
            logger.debug(f"Not setting {key_path}, inherited from workspace.")
            return

        if not value:  # remove value and clean up the sub-dict
            self._get_property(key_path, remove=True)
            return

        # get the tomlkit object of the section
        dat = self._get_property([])

        # dig down, create missing nested objects on the fly
        curr = dat
        for path_key in key_path[:-1]:
            if path_key not in curr:
                curr.add(path_key, table())
            curr = curr[path_key]

        # Handle arrays with proper formatting
        if isinstance(value, list):
            arr = toml_array(value)
            curr[key_path[-1]] = arr
        else:
            curr[key_path[-1]] = value

    @staticmethod
    def _from_person(person: Person | Entity):
        """Convert project metadata person object to rust string for person format "full name <email>."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person_obj: str) -> Person | Entity | None:
        """Parse rust person string to a Person. It has format "full name <email>." but email is optional.

        Since there is no way to know whether this entry is a person or an entity, we will directly convert to Person.
        """
        return parse_name_email(person_obj)

    @classmethod
    def _parse_people(cls, people: list[Any] | None) -> list[Person | Entity]:
        """Return a list of Persons parsed from list of format-specific people representations. to_person can return None, so filter out None values."""
        return list(filter(None, map(cls._to_person, people or [])))

    @property
    def keywords(self) -> list[str] | None:
        """Return the keywords of the project."""
        return self._get_property(self._get_key("keywords"))

    @keywords.setter
    def keywords(self, keywords: list[str]) -> None:
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
        if self._get_property(self._get_key("license_file")):
            self.license = None
