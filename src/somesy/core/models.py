"""Core models for the somesy package."""

from __future__ import annotations

import functools
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)
from rich.pretty import pretty_repr
from typing_extensions import Annotated

from .core import get_input_content
from .log import SomesyLogLevel
from .types import ContributionTypeEnum, Country, HttpUrlStr, LicenseEnum

# --------
# Somesy configuration model


class SomesyBaseModel(BaseModel):
    """Customized pydantic BaseModel for somesy.

    Apart from some general tweaks for better defaults,
    adds a private `_key_order` field, which is used to track the
    preferred order for serialization (usually coming from some existing input).

    It can be set on an instance using the set_key_order method,
    and is preserved by `copy()`.

    NOTE: The custom order is intended for leaf models (no further nested models),
    custom order will not work correctly across nesting layers.
    """

    model_config = dict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        str_min_length=1,
    )

    # ----
    # Key order magic

    _key_order: List[str] = PrivateAttr([])
    """List of field names (NOT aliases!) in the order they should be written in."""

    @classmethod
    @functools.lru_cache()  # compute once per class
    def _aliases(cls) -> Dict[str, str]:
        """Map back from alias field names to internal field names."""
        return {v.alias or k: k for k, v in cls.model_fields.items()}

    @classmethod
    def make_partial(cls, dct):
        """Construct unvalidated partial model from dict.

        Handles aliases correctly, unlike `construct`.
        """
        un_alias = cls._aliases()
        return cls.model_construct(**{un_alias.get(k) or k: v for k, v in dct.items()})

    def set_key_order(self, keys: List[str]):
        """Setter for custom key order used in serialization."""
        un_alias = self._aliases()
        # make sure we use the _actual_ field names
        self._key_order = list(map(lambda k: un_alias.get(k) or k, keys))

    def model_copy(self, *args, **kwargs):
        """Patched copy method (to preserve custom key order)."""
        ret = super().model_copy(*args, **kwargs)
        ret.set_key_order(list(self._key_order))
        return ret

    @staticmethod
    def _patch_kwargs_defaults(kwargs):
        """Set some default arguments if they are not set by kwargs."""
        for key in ["exclude_defaults", "exclude_none"]:
            if kwargs.get(key, None) is None:
                kwargs[key] = True

    def _reorder_dict(self, dct):
        """Return dict with patched key order (according to `self._key_order`).

        Keys in `dct` not listed in `self._key_order` come after all others.

        Used to patch up `model_dump()` and `model_dump_json()`.
        """
        key_order = self._key_order or []
        existing = set(key_order).intersection(set(dct.keys()))
        key_order = [k for k in key_order if k in existing]
        key_order += list(set(dct.keys()) - set(key_order))
        return {k: dct[k] for k in key_order}

    def model_dump(self, *args, **kwargs):
        """Patched dict method (to preserve custom key order)."""
        self._patch_kwargs_defaults(kwargs)
        by_alias = kwargs.pop("by_alias", False)

        dct = super().model_dump(*args, **kwargs, by_alias=False)
        ret = self._reorder_dict(dct)

        if by_alias:
            ret = {self.model_fields[k].alias or k: v for k, v in ret.items()}
        return ret

    def model_dump_json(self, *args, **kwargs):
        """Patched json method (to preserve custom key order)."""
        self._patch_kwargs_defaults(kwargs)
        by_alias = kwargs.pop("by_alias", False)

        # loop back json through dict to apply custom key order
        dct = json.loads(super().model_dump_json(*args, **kwargs, by_alias=False))
        ret = self._reorder_dict(dct)

        if by_alias:
            ret = {self.model_fields[k].alias or k: v for k, v in ret.items()}
        return json.dumps(ret, ensure_ascii=False)


_SOMESY_TARGETS = [
    "cff",
    "pyproject",
    "package_json",
    "codemeta",
    "julia",
    "fortran",
    "pom_xml",
    "mkdocs",
    "rust",
]


class SomesyConfig(SomesyBaseModel):
    """Pydantic model for somesy tool configuration.

    Note that all fields match CLI options, and CLI options will override the
    values declared in a somesy input file (such as `somesy.toml`).
    """

    @model_validator(mode="before")
    @classmethod
    def at_least_one_target(cls, values):
        """Check that at least one output file is enabled."""
        if all(map(lambda x: values.get(f"no_sync_{x}"), _SOMESY_TARGETS)):
            msg = "No sync target enabled, nothing to do. Probably this is a mistake?"
            raise ValueError(msg)

        return values

    # cli flags
    show_info: Annotated[
        bool,
        Field(
            description="Show basic information messages on run (-v flag).",
        ),
    ] = False
    verbose: Annotated[
        bool, Field(description="Show verbose messages on run (-vv flag).")
    ] = False
    debug: Annotated[
        bool, Field(description="Show debug messages on run (-vvv flag).")
    ] = False

    input_file: Annotated[
        Optional[Path], Field(description="Project metadata input file path.")
    ] = Path("somesy.toml")

    no_sync_pyproject: Annotated[
        bool, Field(description="Do not sync with pyproject.toml.")
    ] = False
    pyproject_file: Annotated[
        Union[Path, List[Path]], Field(description="pyproject.toml file path.")
    ] = Path("pyproject.toml")

    no_sync_package_json: Annotated[
        bool, Field(description="Do not sync with package.json.")
    ] = False
    package_json_file: Annotated[
        Union[Path, List[Path]], Field(description="package.json file path.")
    ] = Path("package.json")

    no_sync_julia: Annotated[
        bool, Field(description="Do not sync with Project.toml.")
    ] = False
    julia_file: Annotated[
        Union[Path, List[Path]], Field(description="Project.toml file path.")
    ] = Path("Project.toml")

    no_sync_fortran: Annotated[
        bool, Field(description="Do not sync with fpm.toml.")
    ] = False
    fortran_file: Annotated[
        Union[Path, List[Path]], Field(description="fpm.toml file path.")
    ] = Path("fpm.toml")

    no_sync_pom_xml: Annotated[bool, Field(description="Do not sync with pom.xml.")] = (
        False
    )
    pom_xml_file: Annotated[
        Union[Path, List[Path]], Field(description="pom.xml file path.")
    ] = Path("pom.xml")

    no_sync_mkdocs: Annotated[
        bool, Field(description="Do not sync with mkdocs.yml.")
    ] = False
    mkdocs_file: Annotated[
        Union[Path, List[Path]], Field(description="mkdocs.yml file path.")
    ] = Path("mkdocs.yml")

    no_sync_rust: Annotated[bool, Field(description="Do not sync with Cargo.toml.")] = (
        False
    )
    rust_file: Annotated[
        Union[Path, List[Path]], Field(description="Cargo.toml file path.")
    ] = Path("Cargo.toml")

    no_sync_cff: Annotated[bool, Field(description="Do not sync with CFF.")] = False
    cff_file: Annotated[
        Union[Path, List[Path]], Field(description="CFF file path.")
    ] = Path("CITATION.cff")

    no_sync_codemeta: Annotated[
        bool, Field(description="Do not sync with codemeta.json.")
    ] = False
    codemeta_file: Annotated[
        Union[Path, List[Path]], Field(description="codemeta.json file path.")
    ] = Path("codemeta.json")
    merge_codemeta: Annotated[
        bool,
        Field(
            description="Merge codemeta.json with with an existing codemeta.json file."
        ),
    ] = False

    # property to pass validation for all inputs/outputs
    pass_validation: Annotated[
        Optional[bool],
        Field(description="Pass validation for all output files."),
    ] = False

    # packages (sub-folders) for monorepos with their own somesy config
    packages: Annotated[
        Optional[Union[Path, List[Path]]],
        Field(
            description="Packages (sub-folders) for monorepos with their own somesy config."
        ),
    ] = None

    def log_level(self) -> SomesyLogLevel:
        """Return log level derived from this configuration."""
        return SomesyLogLevel.from_flags(
            info=self.show_info, verbose=self.verbose, debug=self.debug
        )

    def update_log_level(self, log_level: SomesyLogLevel):
        """Update config flags according to passed log level."""
        self.show_info = log_level == SomesyLogLevel.INFO
        self.verbose = log_level == SomesyLogLevel.VERBOSE
        self.debug = log_level == SomesyLogLevel.DEBUG

    def get_input(self) -> SomesyInput:
        """Based on the somesy config, load the complete somesy input."""
        # get metadata+config from specified input file
        somesy_input = SomesyInput.from_input_file(self.input_file)
        # update input with merged config settings (cli overrides config file)
        dct: Dict[str, Any] = {}
        dct.update(somesy_input.config or {})
        dct.update(self.model_dump())
        somesy_input.config = SomesyConfig(**dct)
        return somesy_input

    def resolve_paths(self, base_dir: Path) -> None:
        """Resolve all paths in the config relative to the given base directory.

        Args:
            base_dir: The base directory to resolve paths against.

        """

        def resolve_path(
            paths: Optional[Union[Path, List[Path]]],
        ) -> Optional[Union[Path, List[Path]]]:
            if paths is None:
                return None
            if isinstance(paths, list):
                return [base_dir / p for p in paths]
            return base_dir / paths

        # Resolve all file paths
        resolved_input = resolve_path(self.input_file)
        self.input_file = resolved_input if isinstance(resolved_input, Path) else None
        self.pyproject_file = resolve_path(self.pyproject_file)
        self.package_json_file = resolve_path(self.package_json_file)
        self.julia_file = resolve_path(self.julia_file)
        self.fortran_file = resolve_path(self.fortran_file)
        self.pom_xml_file = resolve_path(self.pom_xml_file)
        self.mkdocs_file = resolve_path(self.mkdocs_file)
        self.rust_file = resolve_path(self.rust_file)
        self.cff_file = resolve_path(self.cff_file)
        self.codemeta_file = resolve_path(self.codemeta_file)
        self.packages = resolve_path(self.packages)


# --------
# Project metadata model (modified from CITATION.cff)


class ContributorBaseModel(SomesyBaseModel):
    """Base model for Person and Entity models.

    This schema is based on CITATION.cff 1.2, modified and extended for the needs of somesy.
    """

    email: Annotated[
        Optional[str],
        Field(
            pattern=r"^[\S]+@[\S]+\.[\S]{2,}$",
            description="The person's email address.",
        ),
    ] = None

    alias: Annotated[Optional[str], Field(description="The contributor's alias.")] = (
        None
    )
    address: Annotated[
        Optional[str], Field(description="The contributor's address.")
    ] = None
    city: Annotated[Optional[str], Field(description="The entity's city.")] = None
    country: Annotated[
        Optional[Country], Field(description="The entity's country.")
    ] = None
    fax: Annotated[Optional[str], Field(description="The person's fax number.")] = None
    post_code: Annotated[
        Optional[str], Field(alias="post-code", description="The entity's post-code.")
    ] = None
    region: Annotated[Optional[str], Field(description="The entity's region.")] = None
    tel: Annotated[Optional[str], Field(description="The entity's phone number.")] = (
        None
    )

    # ----
    # somesy-specific extensions
    author: Annotated[
        bool,
        Field(
            description="Indicates whether the entity is an author of the project (i.e. significant contributor)."
        ),
    ] = False
    publication_author: Annotated[
        Optional[bool],
        Field(
            description="Indicates whether the entity is to be listed as an author in academic citations."
        ),
    ] = None
    maintainer: Annotated[
        bool,
        Field(
            description="Indicates whether the entity is a maintainer of the project (i.e. for contact)."
        ),
    ] = False

    # NOTE: CFF 1.3 (once done) might provide ways for refined contributor description. That should be implemented here.
    contribution: Annotated[
        Optional[str],
        Field(description="Summary of how the entity contributed to the project."),
    ] = None
    contribution_types: Annotated[
        Optional[List[ContributionTypeEnum]],
        Field(
            description="Relevant types of contributions (see https://allcontributors.org/docs/de/emoji-key).",
            min_length=1,
        ),
    ] = None
    contribution_begin: Annotated[
        Optional[date], Field(description="Beginning date of the contribution.")
    ] = None
    contribution_end: Annotated[
        Optional[date], Field(description="Ending date of the contribution.")
    ] = None

    @model_validator(mode="before")
    @classmethod
    def author_implies_publication(cls, values):
        """Ensure consistency of author and publication_author."""
        if values.get("author"):
            # NOTE: explicitly check for False (different case from None = missing!)
            if values.get("publication_author") is False:
                msg = "Combining author=true and publication_author=false is invalid!"
                raise ValueError(msg)
            values["publication_author"] = True
        return values

    # helper methods
    @property
    def full_name(self) -> str:
        """Return the name of the contributor."""
        pass

    def to_name_email_string(self) -> str:
        """Convert project metadata person object to poetry string for person format `full name <x@y.z>`."""
        if self.email:
            return f"{self.full_name} <{self.email}>"
        else:
            return self.full_name

    @classmethod
    def from_name_email_string(cls, person: str):
        """Return the type of class based on an name/e-mail string like `full name <x@y.z>`.

        If the name is `A B C`, then `A B` will be the given names and `C` will be the family name.
        """
        pass


class Entity(ContributorBaseModel):
    """Metadata about an entity in the context of a software project ownership.

    An entity, i.e., an institution, team, research group, company, conference, etc., as opposed to a single natural person.
    This schema is based on CITATION.cff 1.2, modified and extended for the needs of somesy.
    """

    # NOTE: we rely on the defined aliases for direct CITATION.cff interoperability.

    date_end: Annotated[
        Optional[date],
        Field(
            alias="date-end",
            description="The entity's ending date, e.g., when the entity is a conference.",
        ),
    ] = None
    date_start: Annotated[
        Optional[date],
        Field(
            alias="date-start",
            description="The entity's starting date, e.g., when the entity is a conference.",
        ),
    ] = None
    location: Annotated[
        Optional[str],
        Field(
            description="The entity's location, e.g., when the entity is a conference."
        ),
    ] = None
    name: Annotated[str, Field(description="The entity's name.")]
    website: Annotated[
        Optional[HttpUrlStr], Field(description="The entity's website.")
    ] = None
    rorid: Annotated[
        Optional[HttpUrlStr],
        Field(
            description="The entity's ROR ID url **(not required, but highly suggested)**."
        ),
    ] = None

    # helper methods
    @property
    def full_name(self) -> str:
        """Use same property as Person for code integration."""
        return self.name

    @classmethod
    def from_name_email_string(cls, entity: str) -> Entity:
        """Return an `Entity` based on an name/e-mail string like `name <x@y.z>`."""
        m = re.match(r"\s*([^<]+)<([^>]+)>", entity)
        if m is None:
            return Entity(**{"name": entity})

        name, mail = (
            m.group(1).strip(),
            m.group(2).strip(),
        )
        return Entity(
            **{
                "name": name,
                "email": mail,
            }
        )

    def same_person(self, other: Entity) -> bool:
        """Return whether two Entity metadata records are about the same real person.

        Uses heuristic match based on email and name (whichever are provided).
        """
        if not isinstance(other, Entity):
            return False
        if self.rorid is not None and other.rorid is not None:
            if self.rorid == other.rorid:
                return True
        if self.website is not None and other.website is not None:
            if self.website == other.website:
                return True
        if self.email is not None and other.email is not None:
            if self.email == other.email:
                return True
        return self.name == other.name

    def model_dump_json(self, *args, **kwargs):
        """Patched json method (to preserve custom key order), remove rorid and set it as website if it is not None."""
        ret = super().model_dump_json(*args, **kwargs)
        # convert ret to dict
        ret = json.loads(ret)
        if self.rorid is not None and "website" not in ret:
            ret["website"] = str(self.rorid)
            ret.pop("rorid")
        # convert ret back to json string
        return json.dumps(ret)


class Person(ContributorBaseModel):
    """Metadata about a person in the context of a software project.

    This schema is based on CITATION.cff 1.2, modified and extended for the needs of somesy.
    """

    # NOTE: we rely on the defined aliases for direct CITATION.cff interoperability.

    orcid: Annotated[
        Optional[HttpUrlStr],
        Field(
            description="The person's ORCID url **(not required, but highly suggested)**."
        ),
    ] = None
    family_names: Annotated[
        str, Field(alias="family-names", description="The person's family names.")
    ]
    given_names: Annotated[
        str, Field(alias="given-names", description="The person's given names.")
    ]
    name_particle: Annotated[
        Optional[str],
        Field(
            alias="name-particle",
            description="The person's name particle, e.g., a nobiliary particle or a preposition meaning 'of' or 'from'"
            " (for example 'von' in 'Alexander von Humboldt').",
            examples=["von"],
        ),
    ] = None
    name_suffix: Annotated[
        Optional[str],
        Field(
            alias="name-suffix",
            description="The person's name-suffix, e.g. 'Jr.' for Sammy Davis Jr. or 'III' for Frank Edwin Wright III.",
            examples=["Jr.", "III"],
        ),
    ] = None
    affiliation: Annotated[
        Optional[str], Field(description="The person's affiliation.")
    ] = None

    # helper methods

    @property
    def full_name(self) -> str:
        """Return the full name of the person."""
        names = []

        if self.given_names:
            names.append(self.given_names)

        if self.name_particle:
            names.append(self.name_particle)

        if self.family_names:
            names.append(self.family_names)

        if self.name_suffix:
            names.append(self.name_suffix)

        return " ".join(names) if names else ""

    @classmethod
    def from_name_email_string(cls, person: str) -> Person:
        """Return a `Person` based on an name/e-mail string like `full name <x@y.z>`.

        If the name is `A B C`, then `A B` will be the given names and `C` will be the family name.
        """
        m = re.match(r"\s*([^<]+)<([^>]+)>", person)
        if m is None:
            names = list(map(lambda s: s.strip(), person.split()))
            return Person(
                **{
                    "given-names": " ".join(names[:-1]),
                    "family-names": names[-1],
                }
            )
        if m is None:
            names = list(map(lambda s: s.strip(), person.split()))
            return Person(
                **{
                    "given-names": " ".join(names[:-1]),
                    "family-names": names[-1],
                }
            )
        names, mail = (
            list(map(lambda s: s.strip(), m.group(1).split())),
            m.group(2).strip(),
        )
        # NOTE: for our purposes, does not matter what are given or family names,
        # we only compare on full_name anyway.
        return Person(
            **{
                "given-names": " ".join(names[:-1]),
                "family-names": names[-1],
                "email": mail,
            }
        )

    def same_person(self, other) -> bool:
        """Return whether two Person metadata records are about the same real person.

        Uses heuristic match based on orcid, email and name (whichever are provided).
        """
        if not isinstance(other, Person):
            return False
        if self.orcid is not None and other.orcid is not None:
            # having orcids is the best case, a real identifier
            # NOTE: converting to str from pydantic-internal Url object for == !
            return str(self.orcid) == str(other.orcid)

        # otherwise, try to match according to mail/name
        # sourcery skip: merge-nested-ifs
        if self.email is not None and other.email is not None:
            if self.email == other.email:
                # an email address belongs to exactly one person
                # => same email -> same person
                return True
            # otherwise, need to check name
            # (a person often has multiple email addresses)

        # no orcids, no/distinct email address
        # -> decide based on full_name (which is always present)
        return self.full_name == other.full_name


class ProjectMetadata(SomesyBaseModel):
    """Pydantic model for Project Metadata Input."""

    model_config = dict(extra="ignore")

    @field_validator("people")
    @classmethod
    def ensure_distinct_people(cls, people):
        """Make sure that no person is listed twice in the same list."""
        for i in range(len(people)):
            for j in range(i + 1, len(people)):
                if people[i].same_person(people[j]):
                    p1 = pretty_repr(json.loads(people[i].model_dump_json()))
                    p2 = pretty_repr(json.loads(people[j].model_dump_json()))
                    msg = f"Same person is listed twice:\n{p1}\n{p2}"
                    raise ValueError(msg)
        return people

    @field_validator("entities")
    @classmethod
    def ensure_distinct_entities(cls, entities):
        """Make sure that no entity is listed twice in the same list."""
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                if entities[i].same_person(entities[j]):
                    e1 = pretty_repr(json.loads(entities[i].model_dump_json()))
                    e2 = pretty_repr(json.loads(entities[j].model_dump_json()))
                    msg = f"Same entity is listed twice:\n{e1}\n{e2}"
                    raise ValueError(msg)
        return entities

    @model_validator(mode="after")
    def at_least_one_author(self) -> ProjectMetadata:
        """Make sure there is at least one author."""
        if not self.people and not self.entities:
            raise ValueError(
                "There have to be at least a person or an organization in the input"
            )
        if not any(map(lambda p: p.author, self.people)) and not any(
            map(lambda e: e.author, self.entities)
        ):
            raise ValueError("At least one person must be an author of this project.")
        return self

    name: Annotated[str, Field(description="Project name.")]
    description: Annotated[str, Field(description="Project description.")]
    version: Annotated[Optional[str], Field(description="Project version.")] = None
    license: Annotated[LicenseEnum, Field(description="SPDX License string.")]

    homepage: Annotated[
        Optional[HttpUrlStr], Field(description="URL of the project homepage.")
    ] = None
    repository: Annotated[
        Optional[HttpUrlStr],
        Field(description="URL of the project source code repository."),
    ] = None
    documentation: Annotated[
        Optional[HttpUrlStr], Field(description="URL of the project documentation.")
    ] = None

    keywords: Annotated[
        Optional[List[str]],
        Field(min_length=1, description="Keywords that describe the project."),
    ] = None

    people: Annotated[
        Optional[List[Person]],
        Field(
            description="Project authors, maintainers and contributors.",
            default_factory=list,
        ),
    ]

    entities: Annotated[
        Optional[List[Entity]],
        Field(
            description="Project authors, maintainers and contributors as entities (organizations).",
            default_factory=list,
        ),
    ]

    def authors(self):
        """Return people and entities explicitly marked as authors."""
        authors = [p for p in self.people if p.author]
        authors.extend([e for e in self.entities if e.author])
        return authors

    def publication_authors(self):
        """Return people marked as publication authors.

        This always includes people marked as authors.
        """
        # return an empty list if no publication authors are specified
        if not any(map(lambda p: p.publication_author, self.people)) and not any(
            map(lambda p: p.publication_author, self.entities)
        ):
            return []
        publication_authors = [p for p in self.people if p.publication_author]
        publication_authors.extend([e for e in self.entities if e.publication_author])
        return publication_authors

    def maintainers(self):
        """Return people and entities marked as maintainers."""
        maintainers = [p for p in self.people if p.maintainer]
        maintainers.extend([e for e in self.entities if e.maintainer])
        return maintainers

    def contributors(self):
        """Return only people and entities not marked as authors."""
        contributors = [p for p in self.people if not p.author]
        contributors.extend([e for e in self.entities if not e.author])
        return contributors


class SomesyInput(SomesyBaseModel):
    """The complete somesy input file (`somesy.toml`) or section (`pyproject.toml`)."""

    _origin: Optional[Path]

    project: Annotated[
        ProjectMetadata,
        Field(description="Project metadata to be used and synchronized."),
    ]
    config: Annotated[
        Optional[SomesyConfig],
        Field(
            description="somesy tool configuration (matches CLI flags).",
            default_factory=lambda: SomesyConfig(),
        ),
    ]

    # if config.input_file is set, use it as origin
    @model_validator(mode="after")
    def set_origin(self):
        """Set the origin of the input file."""
        if self.config and self.config.input_file:
            self._origin = self.config.input_file

    def is_somesy_file(self) -> bool:
        """Return whether this somesy input is from a somesy config file.

        That means, returns False if it is from pyproject.toml or package.json.
        """
        return self.is_somesy_file_path(self._origin or Path("."))

    @classmethod
    def is_somesy_file_path(cls, path: Path) -> bool:
        """Return whether the path looks like a somesy config file.

        That means, returns False if it is e.g. pyproject.toml or package.json.
        """
        return str(path).endswith("somesy.toml")

    @classmethod
    def from_input_file(cls, path: Path) -> SomesyInput:
        """Load somesy input from given file."""
        content = get_input_content(path)
        ret = SomesyInput(**content)
        ret._origin = path
        return ret
