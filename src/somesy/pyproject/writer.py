"""Pyproject writers for setuptools and poetry."""

import logging
from pathlib import Path
from typing import Any

import tomlkit
import wrapt
from rich.pretty import pretty_repr
from tomlkit import load

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import IgnoreKey, ProjectMetadataWriter

from .models import License, PoetryConfig, SetuptoolsConfig

logger = logging.getLogger("somesy")


def license_expression(licenses) -> str:
    """Convert one or more license identifiers to an SPDX expression."""
    return " OR ".join(
        str(license)
        for license in (licenses if isinstance(licenses, list) else [licenses])
    )


class PyprojectCommon(ProjectMetadataWriter):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(
        self,
        path: Path,
        *,
        section: list[str],
        model_cls,
        direct_mappings=None,
        pass_validation: bool | None = False,
    ):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self._model_cls = model_cls
        self._section = section
        super().__init__(
            path,
            create_if_not_exists=False,
            direct_mappings=direct_mappings or {},
            pass_validation=pass_validation,
        )

    @property
    def _dynamic_fields(self) -> list[str]:
        """Return the list of fields marked as dynamic in pyproject.toml."""
        return self._get_property(["dynamic"]) or []

    @property
    def version(self) -> str | None:
        """Return the version of the project."""
        return self._get_property(self._get_key("version"))

    @version.setter
    def version(self, value: str) -> None:
        """Set version, skipping if listed as dynamic."""
        if "version" in self._dynamic_fields:
            if value:
                logger.warning(
                    "Field 'version' is listed as dynamic — skipping sync from somesy."
                )
            return
        self._set_property(self._get_key("version"), value)

    @property
    def description(self) -> str | None:
        """Return the description of the project."""
        return self._get_property(self._get_key("description"))

    @description.setter
    def description(self, value: str) -> None:
        """Set description, skipping if listed as dynamic."""
        if "description" in self._dynamic_fields:
            if value:
                logger.warning(
                    "Field 'description' is listed as dynamic — skipping sync from somesy."
                )
            return
        self._set_property(self._get_key("description"), value)

    def _load(self) -> None:
        """Load pyproject.toml file."""
        with open(self.path) as f:
            self._data = tomlkit.load(f)

    def _validate(self) -> None:
        """Validate poetry config using pydantic class.

        In order to preserve toml comments and structure, tomlkit library is used.
        Pydantic class only used for validation.
        """
        if self.pass_validation:
            return
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {self._model_cls.__name__}: {pretty_repr(config)}"
        )
        self._model_cls(**config)

    def save(self, path: Path | None = None) -> None:
        """Save the pyproject file."""
        path = path or self.path

        with open(path, "w") as f:
            tomlkit.dump(self._data, f)

    def _get_property(
        self, key: str | list[str], *, remove: bool = False, **kwargs
    ) -> Any | None:
        """Get a property from the pyproject.toml file."""
        key_path = [key] if isinstance(key, str) else key
        full_path = self._section + key_path
        return super()._get_property(full_path, remove=remove, **kwargs)

    def _set_property(self, key: str | list[str] | IgnoreKey, value: Any) -> None:
        """Set a property in the pyproject.toml file."""
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
        for path_key in key_path[:-1]:
            if path_key not in curr:
                curr.add(path_key, tomlkit.table())
            curr = curr[path_key]

        # Handle arrays with proper formatting
        if isinstance(value, list):
            array = tomlkit.array()
            array.extend(value)
            array.multiline(True)
            # Ensure whitespace after commas in inline tables
            for item in array:
                if isinstance(item, tomlkit.items.InlineTable):
                    # Rebuild the inline table with desired formatting
                    formatted_item = tomlkit.inline_table()
                    for k, v in item.value.items():
                        formatted_item[k] = v
                    formatted_item.trivia.trail = " "  # Add space after each comma
                    array[array.index(item)] = formatted_item
            curr[key_path[-1]] = array
        else:
            curr[key_path[-1]] = value


class Poetry(PyprojectCommon):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: bool | None = False,
        version: int | None = 1,
    ):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self._poetry_version = version
        v2_mappings = {
            "homepage": ["urls", "homepage"],
            "repository": ["urls", "repository"],
            "documentation": ["urls", "documentation"],
            "license": ["license", "text"],
        }
        if version == 1:
            super().__init__(
                path,
                section=["tool", "poetry"],
                model_cls=PoetryConfig,
                pass_validation=pass_validation,
            )
        else:
            super().__init__(
                path,
                section=["project"],
                model_cls=PoetryConfig,
                pass_validation=pass_validation,
                direct_mappings=v2_mappings,
            )

    @staticmethod
    def _from_person(person: Person | Entity, poetry_version: int = 1):
        """Convert project metadata person object to poetry string for person format "full name <email>."""
        if poetry_version == 1:
            return person.to_name_email_string()
        else:
            response = {"name": person.full_name}
            if person.email:
                response["email"] = person.email
            return response

    @staticmethod
    def _to_person(
        person: str | dict[str, str],
    ) -> Person | Entity | None:
        """Convert from free string to person or entity object."""
        if isinstance(person, dict):
            temp = str(person["name"])
            if "email" in person:
                temp = f"{temp} <{person['email']}>"
            person = temp
        try:
            return Person.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.info(f"Cannot convert {person} to Person object, trying Entity.")

        try:
            return Entity.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person} to Entity.")
            return None

    @property
    def license(self) -> License | str | None:
        """Get license from pyproject.toml file."""
        raw_license = self._get_property(["license"])
        if self._poetry_version == 1:
            return raw_license
        if raw_license is None:
            return None
        if isinstance(raw_license, str):
            return raw_license
        return raw_license

    @license.setter
    def license(self, value: License | str) -> None:
        """Set license in pyproject.toml file."""
        # if version is 1, set license as str
        if self._poetry_version == 1:
            self._set_property(["license"], value)
        else:
            self._set_property(["license"], value)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync metadata with pyproject.toml file."""
        # Store original _from_person method
        original_from_person = self._from_person

        # Override _from_person to include poetry_version
        self._from_person = lambda person: original_from_person(  # type: ignore
            person, poetry_version=self._poetry_version
        )

        # Call parent sync method
        super().sync(metadata)

        # Restore original _from_person method
        self._from_person = original_from_person  # type: ignore

        self.license = license_expression(metadata.license)

        # For Poetry v2, convert authors and maintainers from array of tables to inline tables
        if self._poetry_version == 2:
            if (
                "description" in self._data["project"]
                and "\n" in self._data["project"]["description"]
            ):
                self._data["project"]["description"] = tomlkit.string(
                    self._data["project"]["description"], multiline=True
                )
            # Move urls section to the end if it exists
            if "urls" in self._data["project"]:
                urls = self._data["project"].pop("urls")
                self._data["project"]["urls"] = urls


class SetupTools(PyprojectCommon):
    """Setuptools config file handler parsed from setup.cfg."""

    def __init__(self, path: Path, pass_validation: bool | None = False):
        """Setuptools config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        section = ["project"]
        mappings = {
            "homepage": ["urls", "homepage"],
            "repository": ["urls", "repository"],
            "documentation": ["urls", "documentation"],
        }
        super().__init__(
            path,
            section=section,
            direct_mappings=mappings,
            model_cls=SetuptoolsConfig,
            pass_validation=pass_validation,
        )

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to setuptools dict for person format."""
        response = {"name": person.full_name}
        if person.email:
            response["email"] = person.email
        return response

    @staticmethod
    def _to_person(person: str | dict) -> Entity | Person | None:
        """Parse setuptools person string to a Person/Entity."""
        # NOTE: for our purposes, does not matter what are given or family names,
        # we only compare on full_name anyway.
        if isinstance(person, dict):
            temp = str(person["name"])
            if "email" in person:
                temp = f"{temp} <{person['email']}>"
            person = temp

        try:
            return Person.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.info(f"Cannot convert {person} to Person object, trying Entity.")

        try:
            return Entity.from_name_email_string(person)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person} to Entity.")
            return None

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync metadata with pyproject.toml file and fix license field."""
        super().sync(metadata)
        self.license = license_expression(metadata.license)


# ----


class Pyproject(wrapt.ObjectProxy):
    """Class for syncing pyproject file with other metadata files."""

    __wrapped__: SetupTools | Poetry

    def __init__(self, path: Path, pass_validation: bool | None = False):
        """Pyproject wrapper class. Wraps either setuptools or poetry.

        Args:
            path (Path): Path to pyproject.toml file.
            pass_validation (bool, optional): Whether to pass validation. Defaults to False.

        Raises:
            FileNotFoundError: Raised when pyproject.toml file is not found.
            ValueError: Neither project nor tool.poetry object is found in pyproject.toml file.

        """
        data = None
        if not path.is_file():
            raise FileNotFoundError(f"pyproject file {path} not found")

        with open(path, "r") as f:
            data = load(f)

        # inspect file to pick suitable project metadata writer
        is_poetry = "tool" in data and "poetry" in data["tool"]
        has_project = "project" in data

        if is_poetry:
            if has_project:
                logger.verbose(
                    "Found Poetry 2.x metadata with project section in pyproject.toml"
                )
            else:
                logger.verbose("Found Poetry 1.x metadata in pyproject.toml")
            self.__wrapped__ = Poetry(
                path, pass_validation=pass_validation, version=2 if has_project else 1
            )
        elif has_project and not is_poetry:
            logger.verbose("Found setuptools-based metadata in pyproject.toml")
            self.__wrapped__ = SetupTools(path, pass_validation=pass_validation)
        else:
            msg = "The pyproject.toml file is ambiguous. For Poetry projects, ensure [tool.poetry] section exists. For setuptools, ensure [project] section exists without [tool.poetry]"
            raise ValueError(msg)

        super().__init__(self.__wrapped__)
