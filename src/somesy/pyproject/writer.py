"""Pyproject writers for PEP 621 `[project]` metadata and Poetry."""

import logging
import re
from pathlib import Path
from typing import Any

import tomlkit
import wrapt
from rich.pretty import pretty_repr
from tomlkit import load
from tomlkit.items import Table

from somesy.core.core import atomic_write
from somesy.core.log import VERBOSE
from somesy.core.models import Entity, Person, ProjectMetadata, parse_name_email
from somesy.core.writer import (
    IgnoreKey,
    ProjectMetadataWriter,
    license_expression,
    multiline_description,
    toml_array,
)

from .models import Pep621Config, PoetryConfig

logger = logging.getLogger("somesy")

SUMMARY_MAX_LENGTH = 512
"""Longest package summary (`description`) that PyPI accepts on upload."""

SUMMARY_LINE_BREAK = re.compile(r"[\r\n]")
"""Line breaks are not allowed in a package summary (core metadata `Summary`)."""


def normalize_url_key(name: str) -> str:
    """Return a `[project.urls]` key in a form that can be compared.

    PEP 621 does not standardize these key names, so the same URL appears as
    "Bug Tracker", "bug-tracker" or "bugtracker" depending on the template the
    project started from.
    """
    return re.sub(r"[\s_-]+", "", name).lower()


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
        self._created_tables: list[Table] = []
        super().__init__(
            path,
            create_if_not_exists=False,
            direct_mappings=direct_mappings or {},
            pass_validation=pass_validation,
        )

    def _get_key(self, key: str) -> str | list[str] | IgnoreKey:
        """Get a key itself, resolving url keys to their spelling in the file."""
        mapped = super()._get_key(key)
        if isinstance(mapped, list) and mapped[:1] == ["urls"]:
            return ["urls", self._url_key(mapped[-1])]
        return mapped

    def _url_key(self, name: str, *, warn: bool = False) -> str:
        """Return the spelling of the `[project.urls]` key `name` to read or write.

        The common project templates capitalize the keys ("Homepage",
        "Bug Tracker"). An existing entry is used whatever its spelling; if
        several spellings of the same key exist, the first one is used. A key
        somesy adds follows the predominant capitalization of the table.
        """
        keys = list(self._get_property(["urls"]) or {})
        matches = [k for k in keys if normalize_url_key(k) == normalize_url_key(name)]
        if matches:
            if warn and len(matches) > 1:
                logger.warning(
                    "Found several spellings of the url '%s' (%s), updating '%s'.",
                    name,
                    ", ".join(f"'{k}'" for k in matches),
                    matches[0],
                )
            return matches[0]
        capitalized = sum(key[:1].isupper() for key in keys)
        if capitalized > len(keys) - capitalized:
            return name.capitalize()
        return name

    def _is_dynamic(self, field: str, value: Any) -> bool:
        """Return whether `field` is dynamic, warning if somesy has a value for it."""
        if field not in self._dynamic_fields:
            return False
        if value:
            logger.warning(
                f"Field '{field}' is listed as dynamic — skipping sync from somesy."
            )
        return True

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
        if self._is_dynamic("version", version):
            return
        self._set_property(self._get_key("version"), version)

    def _keeps_license(self, current: Any) -> bool:
        """Tell if the license must be left alone (`file` table or `license-files`)."""
        return (isinstance(current, dict) and "file" in current) or bool(
            self._get_property(["license-files"])
        )

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
        """Set the license of the project.

        A `license = { file = ... }` table or `license-files` in the file are
        left untouched, somesy only manages the SPDX expression. A
        `license = { text = ... }` table is replaced by the expression.
        """
        if self._is_dynamic("license", license):
            return
        current = self._get_property(["license"])
        if self._keeps_license(current):
            if license:
                logger.warning(
                    "The license of the pyproject file was kept, it is given as a "
                    "table or with 'license-files' and somesy does not update it."
                )
            return
        self._set_property(["license"], license)

    def _person_entries(self, people: list[Person | Entity]) -> list[Any]:
        """Convert people to the representation used in the file."""
        return [self._from_person(person) for person in people]

    @property
    def authors(self):
        """Return the authors of the project."""
        return super().authors

    @authors.setter
    def authors(self, authors: list[Person | Entity]) -> None:
        """Set authors, skipping if listed as dynamic."""
        if not self._is_dynamic("authors", authors):
            self._set_property(self._get_key("authors"), self._person_entries(authors))

    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        return super().maintainers

    @maintainers.setter
    def maintainers(self, maintainers: list[Person | Entity]) -> None:
        """Set maintainers, skipping if listed as dynamic."""
        if not self._is_dynamic("maintainers", maintainers):
            self._set_property(
                self._get_key("maintainers"), self._person_entries(maintainers)
            )

    @property
    def keywords(self) -> list[str] | None:
        """Return the keywords of the project."""
        return super().keywords

    @keywords.setter
    def keywords(self, keywords: list[str]) -> None:
        """Set keywords, skipping if listed as dynamic."""
        if not self._is_dynamic("keywords", keywords):
            self._set_property(self._get_key("keywords"), keywords)

    def _set_url(self, field: str, value: str | None) -> None:
        """Set a project url, skipping if `urls` is listed as dynamic."""
        if self._is_dynamic("urls", value):
            return
        key = self._get_key(field)
        if isinstance(key, list):
            self._url_key(key[-1], warn=True)
        self._set_property(key, value)

    @property
    def homepage(self) -> str | None:
        """Return the homepage url of the project."""
        return super().homepage

    @homepage.setter
    def homepage(self, value: str | None) -> None:
        """Set the homepage url of the project."""
        self._set_url("homepage", value)

    @property
    def repository(self) -> str | dict | None:
        """Return the repository url of the project."""
        return super().repository

    @repository.setter
    def repository(self, value: str | dict | None) -> None:
        """Set the repository url of the project."""
        self._set_url("repository", value)  # type: ignore[arg-type]

    @property
    def documentation(self) -> str | dict | None:
        """Return the documentation url of the project."""
        return super().documentation

    @documentation.setter
    def documentation(self, value: str | dict | None) -> None:
        """Set the documentation url of the project."""
        self._set_url("documentation", value)  # type: ignore[arg-type]

    @property
    def description(self) -> str | None:
        """Return the description of the project."""
        return self._get_property(self._get_key("description"))

    @description.setter
    def description(self, description: str) -> None:
        """Set description, skipping if listed as dynamic."""
        if self._is_dynamic("description", description):
            return
        if description and (
            len(description) > SUMMARY_MAX_LENGTH
            or SUMMARY_LINE_BREAK.search(description)
        ):
            logger.warning(
                "Field 'description' becomes the package summary, which must be a "
                "single line of at most %d characters to be uploaded to PyPI. "
                "Put a longer text in the 'abstract' field instead.",
                SUMMARY_MAX_LENGTH,
            )
        self._set_property(self._get_key("description"), description)

    def _load(self) -> None:
        """Load pyproject.toml file."""
        with open(self.path, encoding="utf-8") as f:
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

        atomic_write(path, tomlkit.dumps(self._data))

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
                table = tomlkit.table()
                curr.add(path_key, table)
                self._created_tables.append(table)
            curr = curr[path_key]

        # Handle arrays with proper formatting
        if isinstance(value, list):
            array = toml_array(value)
            curr[key_path[-1]] = array
        else:
            curr[key_path[-1]] = value

        if any(curr is table for table in self._created_tables):
            for field in curr:
                curr.item(field).trivia.trail = "\n"
            curr.item(list(curr)[-1]).trivia.trail = "\n\n"


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
        version = version or 1
        self._poetry_version = version
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
            return _pep621_person(person)

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
        return parse_name_email(person_obj)

    def _person_entries(self, people: list[Person | Entity]) -> list[Any]:
        """Convert people to the person format of the Poetry version."""
        return [self._from_person(person, self._poetry_version) for person in people]

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync metadata with pyproject.toml file."""
        super().sync(metadata)

        # For Poetry v2, convert authors and maintainers from array of tables to inline tables
        if self._poetry_version == 2:
            multiline_description(self._data["project"])
            # Move urls section to the end if it exists
            if "urls" in self._data["project"]:
                urls = self._data["project"].pop("urls")
                self._data["project"]["urls"] = urls
            self._sync_legacy_metadata(metadata)

    def _sync_legacy_metadata(self, metadata: ProjectMetadata) -> None:
        """Update the deprecated metadata keys that exist in `[tool.poetry]`.

        Poetry 2.x still accepts them, so they must not go stale next to
        `[project]`. Keys that are absent are never added.
        """
        legacy = self._data.get("tool", {}).get("poetry")
        if legacy is None:
            return
        dynamic = self._dynamic_fields

        def update(key: str, value: Any, field: str | None = None) -> None:
            if not value or key not in legacy or (field or key) in dynamic:
                return
            if isinstance(value, list):
                if list(legacy[key]) != value:
                    legacy[key] = toml_array(value)
            elif legacy[key] != value:
                legacy[key] = value

        update("name", metadata.name)
        update("version", metadata.version)
        update("description", metadata.description)

        if metadata.license and not self._keeps_license(
            self._get_property(["license"])
        ):
            update("license", license_expression(metadata.license))

        update("keywords", list(metadata.keywords or []))

        for role, new in (
            ("authors", metadata.authors()),
            ("maintainers", metadata.maintainers()),
        ):
            if role not in legacy or role in dynamic:
                continue
            if role == "authors" and not new:
                continue
            people = self._sync_person_list(list(legacy[role]), new)
            update(role, [p.to_name_email_string() for p in people])
            if not people:
                del legacy[role]

        urls = {
            "homepage": metadata.homepage,
            "repository": metadata.repository,
            "documentation": metadata.documentation,
        }
        for key, url in urls.items():
            if url:
                update(key, str(url), "urls")
        if "urls" in legacy and "urls" not in dynamic:
            for old_key in legacy["urls"]:
                url = urls.get(normalize_url_key(old_key))
                if url and legacy["urls"][old_key] != str(url):
                    legacy["urls"][old_key] = str(url)


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
        return _pep621_person(person)

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

        return parse_name_email(person_obj)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync metadata with pyproject.toml file and fix license field."""
        super().sync(metadata)


def _pep621_person(person: Person | Entity) -> dict[str, str]:
    """Convert a person/entity to a PEP 621 person table."""
    response = {"name": person.full_name}
    if person.email:
        response["email"] = person.email
    return response


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

        with open(path, "r", encoding="utf-8") as f:
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
