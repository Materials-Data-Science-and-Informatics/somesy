"""Pyproject writers for setuptools and poetry."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import tomlkit
import wrapt
from rich.pretty import pretty_repr
from tomlkit import load

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import IgnoreKey, ProjectMetadataWriter

from .models import PoetryConfig, SetuptoolsConfig

logger = logging.getLogger("somesy")


class PyprojectCommon(ProjectMetadataWriter):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(
        self,
        path: Path,
        *,
        section: List[str],
        model_cls,
        direct_mappings=None,
        pass_validation: Optional[bool] = False,
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

    def save(self, path: Optional[Path] = None) -> None:
        """Save the pyproject file."""
        path = path or self.path
        with open(path, "w") as f:
            tomlkit.dump(self._data, f)

    def _get_property(
        self, key: Union[str, List[str]], *, remove: bool = False, **kwargs
    ) -> Optional[Any]:
        """Get a property from the pyproject.toml file."""
        key_path = [key] if isinstance(key, str) else key
        full_path = self._section + key_path
        return super()._get_property(full_path, remove=remove, **kwargs)

    def _set_property(self, key: Union[str, List[str], IgnoreKey], value: Any) -> None:
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
        for key in key_path[:-1]:
            if key not in curr:
                curr.add(key, tomlkit.table())
            curr = curr[key]
        curr[key_path[-1]] = value


class Poetry(PyprojectCommon):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(
        self,
        path: Path,
        pass_validation: Optional[bool] = False,
        version: Optional[int] = 1,
    ):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
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
    def _from_person(person: Union[Person, Entity], poetry_version: int = 1):
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
        person: Union[str, Dict[str, str]],
    ) -> Optional[Union[Person, Entity]]:
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

        # For Poetry v2, convert authors and maintainers from array of tables to inline tables
        if self._poetry_version == 2:
            for field in ["authors", "maintainers"]:
                field_value = self._get_property([field])
                if field_value:
                    # Create an inline array of tables
                    inline_array = tomlkit.array()
                    inline_array.multiline(False)

                    # Convert each table to an inline table and add to array
                    for item in field_value:
                        inline_table = tomlkit.inline_table()
                        for k, v in item.items():
                            inline_table[k] = v
                        inline_array.append(inline_table)

                    # Replace the array of tables with the inline array
                    self._set_property(field, inline_array)


class SetupTools(PyprojectCommon):
    """Setuptools config file handler parsed from setup.cfg."""

    def __init__(self, path: Path, pass_validation: Optional[bool] = False):
        """Setuptools config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        section = ["project"]
        mappings = {
            "homepage": ["urls", "homepage"],
            "repository": ["urls", "repository"],
            "documentation": ["urls", "documentation"],
            "license": ["license", "text"],
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
    def _to_person(person: Union[str, dict]) -> Optional[Union[Entity, Person]]:
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

        # if license field has both text and file, remove file
        if (
            self._get_property(["license", "file"]) is not None
            and self._get_property(["license", "text"]) is not None
        ):
            # delete license file property
            self._data["project"]["license"].pop("file")


# ----


class Pyproject(wrapt.ObjectProxy):
    """Class for syncing pyproject file with other metadata files."""

    __wrapped__: Union[SetupTools, Poetry]

    def __init__(self, path: Path, pass_validation: Optional[bool] = False):
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
