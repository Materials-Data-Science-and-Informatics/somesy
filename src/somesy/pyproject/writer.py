"""Pyproject writers for PEP 621 `[project]` metadata and Poetry."""

import logging
import re
from pathlib import Path
from typing import Any

import tomlkit
import wrapt
from rich.pretty import pretty_repr
from tomlkit import load
from tomlkit.items import InlineTable

from somesy.core.log import VERBOSE
from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import IgnoreKey, ProjectMetadataWriter

from .models import Pep621Config, PoetryConfig

logger = logging.getLogger("somesy")


def normalize_url_key(name: str) -> str:
    """Return a `[project.urls]` key in a form that can be compared.

    PEP 621 does not standardize these key names, so the same URL appears as
    "Bug Tracker", "bug-tracker" or "bugtracker" depending on the template the
    project started from.
    """
    return re.sub(r"[\s_-]+", "", name).lower()


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
        self._adopt_url_key_spelling()

    def _adopt_url_key_spelling(self) -> None:
        """Point the url mappings at the key spellings used in the file.

        The common project templates capitalize the `[project.urls]` keys
        ("Homepage", "Bug Tracker"). Without this, somesy would neither read
        those entries nor update them, and would instead write a second,
        differently spelled entry next to them. A key somesy adds follows the
        capitalization of the keys already there, to keep the table uniform.
        """
        keys = list(self._get_property(["urls"]) or {})
        existing = {normalize_url_key(key): key for key in keys}
        capitalized = bool(keys) and all(key[:1].isupper() for key in keys)
        for field, key_path in self.direct_mappings.items():
            if not isinstance(key_path, list) or key_path[:1] != ["urls"]:
                continue
            name = key_path[-1]
            spelling = existing.get(normalize_url_key(name))
            if spelling is None and capitalized:
                spelling = name.capitalize()
            if spelling is not None:
                self.direct_mappings[field] = ["urls", spelling]

    @property
    def _dynamic_fields(self) -> list[str]:
        """Return the list of fields marked as dynamic in pyproject.toml."""
        return self._get_property(["dynamic"]) or []

    @property
    def version(self) -> str | None:
        """Return the version of the project."""
        return self._get_property(self._get_key("version"))

    @version.setter
    def version(self, version: str | None) -> None:
        """Set version, skipping if listed as dynamic."""
        if "version" in self._dynamic_fields:
            if version:
                logger.warning(
                    "Field 'version' is listed as dynamic — skipping sync from somesy."
                )
            return
        self._set_property(self._get_key("version"), version)

    @property
    def license(self) -> str | None:
        """Return the license of the project as an SPDX expression.

        PEP 639 replaced the `license = { text = ... }` table with a plain
        expression, but files predating it are still valid and must be read.
        A `{ file = ... }` table names a license file instead of an
        identifier, so there is no expression to report.
        """
        license = self._get_property(["license"])
        if isinstance(license, dict):
            return license.get("text")
        return license

    @license.setter
    def license(self, license: str | None) -> None:
        """Set the license of the project."""
        self._set_property(["license"], license)

    @property
    def description(self) -> str | None:
        """Return the description of the project."""
        return self._get_property(self._get_key("description"))

    @description.setter
    def description(self, description: str) -> None:
        """Set description, skipping if listed as dynamic."""
        if "description" in self._dynamic_fields:
            if description:
                logger.warning(
                    "Field 'description' is listed as dynamic — skipping sync from somesy."
                )
            return
        self._set_property(self._get_key("description"), description)

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
        self, key: str | list[str] | IgnoreKey, *, remove: bool = False, **kwargs
    ) -> Any:
        """Get a property from the pyproject.toml file."""
        if isinstance(key, IgnoreKey):
            return None
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
                if isinstance(item, InlineTable):
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
        self._poetry_version = version or 1
        v2_mappings = {
            "homepage": ["urls", "homepage"],
            "repository": ["urls", "repository"],
            "documentation": ["urls", "documentation"],
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
        person_obj: str | dict[str, str],
    ) -> Person | Entity | None:
        """Convert from free string to person or entity object."""
        if isinstance(person_obj, dict):
            temp = str(person_obj["name"])
            if "email" in person_obj:
                temp = f"{temp} <{person_obj['email']}>"
            person_obj = temp
        try:
            return Person.from_name_email_string(person_obj)
        except (ValueError, AttributeError):
            logger.info(f"Cannot convert {person_obj} to Person object, trying Entity.")

        try:
            return Entity.from_name_email_string(person_obj)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person_obj} to Entity.")
            return None

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

        if metadata.license:
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


class Pep621(PyprojectCommon):
    """Handler for PEP 621 `[project]` metadata in pyproject.toml.

    This covers every backend that stores its metadata in the standard
    `[project]` table, i.e. uv, hatchling, flit, PDM, setuptools and
    Poetry 2.x. Only Poetry 1.x needs its own handler, see [somesy.pyproject.writer.Poetry][].
    """

    def __init__(self, path: Path, pass_validation: bool | None = False):
        """PEP 621 `[project]` config file handler parsed from pyproject.toml.

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
            model_cls=Pep621Config,
            pass_validation=pass_validation,
        )

    @staticmethod
    def _from_person(person: Person | Entity):
        """Convert project metadata person object to a PEP 621 person table."""
        response = {"name": person.full_name}
        if person.email:
            response["email"] = person.email
        return response

    @staticmethod
    def _to_person(person_obj: str | dict) -> Entity | Person | None:
        """Parse a PEP 621 person entry to a Person/Entity."""
        # NOTE: for our purposes, does not matter what are given or family names,
        # we only compare on full_name anyway.
        if isinstance(person_obj, dict):
            temp = str(person_obj["name"])
            if "email" in person_obj:
                temp = f"{temp} <{person_obj['email']}>"
            person_obj = temp

        try:
            return Person.from_name_email_string(person_obj)
        except (ValueError, AttributeError):
            logger.info(f"Cannot convert {person_obj} to Person object, trying Entity.")

        try:
            return Entity.from_name_email_string(person_obj)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person_obj} to Entity.")
            return None

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync metadata with pyproject.toml file and fix license field."""
        super().sync(metadata)
        if metadata.license:
            self.license = license_expression(metadata.license)


def _builds_with_poetry(data: Any) -> bool:
    """Return whether the project declares a Poetry build backend.

    Only used to tell a Poetry 2.x project apart from a project of another
    backend that kept a `[tool.poetry]` section for its dependencies, for
    example while migrating away from Poetry. Without a build backend we
    cannot tell, and assume Poetry as before.
    """
    backend = data.get("build-system", {}).get("build-backend")
    return not backend or "poetry" in str(backend)


# ----


class Pyproject(wrapt.ObjectProxy):
    """Class for syncing pyproject file with other metadata files."""

    __wrapped__: Pep621 | Poetry

    def __init__(self, path: Path, pass_validation: bool | None = False):
        """Pyproject wrapper class. Wraps either PEP 621 `[project]` or Poetry metadata.

        The handler is picked based on the metadata tables present in the file,
        not on the configured build backend.

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

        if is_poetry and has_project and not _builds_with_poetry(data):
            # another backend builds the project, so it reads the metadata from
            # [project] and what remains in [tool.poetry] is only configuration
            logger.log(
                VERBOSE,
                "Ignoring the tool.poetry section, the project is not built with Poetry",
            )
            is_poetry = False

        if is_poetry:
            if has_project:
                logger.log(
                    VERBOSE,
                    "Found Poetry 2.x metadata with project section in pyproject.toml",
                )
            else:
                logger.log(VERBOSE, "Found Poetry 1.x metadata in pyproject.toml")
            self.__wrapped__ = Poetry(
                path, pass_validation=pass_validation, version=2 if has_project else 1
            )
        elif has_project and not is_poetry:
            # brackets are escaped, the log handler renders rich markup
            logger.log(VERBOSE, "Found PEP 621 \\[project] metadata in pyproject.toml")
            self.__wrapped__ = Pep621(path, pass_validation=pass_validation)
        else:
            msg = (
                "The pyproject.toml file is ambiguous. Ensure it has either a PEP 621 "
                "[project] section (uv, hatchling, flit, PDM, setuptools, Poetry 2.x) "
                "or a [tool.poetry] section (Poetry 1.x)."
            )
            raise ValueError(msg)

        super().__init__(self.__wrapped__)
