"""Pyproject writers for setuptools and poetry."""

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

import tomlkit
import wrapt
from rich.pretty import pretty_repr
from tomlkit import load

from somesy.core.models import Person, ProjectMetadata
from somesy.core.writer import IgnoreKey, ProjectMetadataWriter

from .models import PoetryConfig, SetuptoolsConfig

logger = logging.getLogger("somesy")


class PyprojectCommon(ProjectMetadataWriter):
    """Poetry config file handler parsed from pyproject.toml."""

    def __init__(
        self, path: Path, *, section: List[str], model_cls, direct_mappings=None
    ):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        self._model_cls = model_cls
        self._section = section
        super().__init__(
            path, create_if_not_exists=False, direct_mappings=direct_mappings or {}
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

    def __init__(self, path: Path):
        """Poetry config file handler parsed from pyproject.toml.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        super().__init__(path, section=["tool", "poetry"], model_cls=PoetryConfig)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to poetry string for person format "full name <email>."""
        return person.to_name_email_string()

    @staticmethod
    def _to_person(person_obj: str) -> Optional[Person]:
        """Parse poetry person string to a Person."""
        try:
            return Person.from_name_email_string(person_obj)
        except (ValueError, AttributeError):
            logger.warning(f"Cannot convert {person_obj} to Person object.")
            return None


class SetupTools(PyprojectCommon):
    """Setuptools config file handler parsed from setup.cfg."""

    def __init__(self, path: Path):
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
            path, section=section, direct_mappings=mappings, model_cls=SetuptoolsConfig
        )

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to setuptools dict for person format."""
        return {"name": person.full_name, "email": person.email}

    @staticmethod
    def _to_person(person_obj) -> Person:
        """Parse setuptools person string to a Person."""
        # NOTE: for our purposes, does not matter what are given or family names,
        # we only compare on full_name anyway.
        names = list(map(lambda s: s.strip(), person_obj["name"].split()))
        return Person(
            **{
                "given-names": " ".join(names[:-1]),
                "family-names": names[-1],
                "email": person_obj["email"].strip(),
            }
        )

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

    def __init__(self, path: Path):
        """Pyproject wrapper class. Wraps either setuptools or poetry.

        Args:
            path (Path): Path to pyproject.toml file.

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
        if "project" in data:
            logger.verbose("Found setuptools-based metadata in pyproject.toml")
            self.__wrapped__ = SetupTools(path)
        elif "tool" in data and "poetry" in data["tool"]:
            logger.verbose("Found poetry-based metadata in pyproject.toml")
            self.__wrapped__ = Poetry(path)
        else:
            msg = "The pyproject.toml file is ambiguous, either add a [project] or [tool.poetry] section"
            raise ValueError(msg)

        super().__init__(self.__wrapped__)
