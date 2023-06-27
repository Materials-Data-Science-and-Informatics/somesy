"""Core models for the somesy package."""
import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Union

from pydantic import (
    AnyUrl,
    BaseModel,
    Extra,
    Field,
    PrivateAttr,
    root_validator,
    validator,
)
from rich.pretty import pretty_repr
from typing_extensions import Annotated

from .types import ContributionTypeEnum, Country, LicenseEnum

# --------
# Somesy configuration model


SOMESY_TARGETS = ["cff", "pyproject", "codemeta"]


class SomesyBaseModel(BaseModel):
    """Customized pydantic BaseModel for somesy.

    Apart from some general tweaks for better defaults,
    adds a private `_key_order` field, which is used to track the
    preferred order for serialization (usually coming from some existing input).
    """

    class Config:
        """Pydantic config."""

        extra = Extra.forbid
        allow_population_by_field_name = True
        underscore_attrs_are_private = True

    _key_order: List[str] = PrivateAttr([])
    """List of keys in the order they should be written in."""

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        """Turn all empty strings into None to treat them as missing."""
        if v == "":
            return None
        return v

    @staticmethod
    def _patch_kwargs_defaults(kwargs):
        for key in ["by_alias", "exclude_defaults", "exclude_none", "exclude_unset"]:
            if not kwargs.get(key):
                kwargs[key] = True

    def _reorder_dict(self, dct):
        """Return dict with patched key order (according to `self._key_order`).

        Keys in `dct` not listed in `self._key_order` come after all others.

        Used to patch up `dict()` and `json()`.
        """
        key_order = self._key_order or []
        existing = set(key_order).intersection(set(dct.keys()))
        key_order = [k for k in key_order if k in existing]
        key_order += list(set(dct.keys()) - set(key_order))
        return {k: dct[k] for k in key_order}

    def dict(self, *args, **kwargs):
        """Patched method to preserve key order."""
        self._patch_kwargs_defaults(kwargs)
        dct = super().dict(*args, **kwargs)
        return self._reorder_dict(dct)

    def json(self, *args, **kwargs):
        """Patched method to preserve key order."""
        self._patch_kwargs_defaults(kwargs)
        # turn into json (to remove pydantic classes)
        dct = json.loads(super().json(*args, **kwargs))
        # loop it back through a dict to reorder keys
        return json.dumps(self._reorder_dict(dct))

    def copy(self, *args, **kwargs):
        """Patched copy to also preserve defined key order."""
        ret = super().copy(*args, **kwargs)
        ret._key_order = list(self._key_order)
        return ret


class SomesyConfig(SomesyBaseModel):
    """Pydantic model for somesy configuration.

    All fields that are not explicitly passed are initialized with default values.
    """

    @root_validator
    def at_least_one_target(cls, values):
        """Check that at least one output file is enabled."""
        if all(map(lambda x: values.get(f"no_sync_{x}"), SOMESY_TARGETS)):
            msg = "No sync target enabled, nothing to do. Probably this is a mistake?"
            raise ValueError(msg)

        return values

    input_file: Path = Field(
        Path(".somesy.toml"), description="Project metadata input file path."
    )

    no_sync_cff: bool = Field(False, description="Do not sync with CFF.")
    cff_file: Path = Field(Path("CITATION.cff"), description="CFF file path.")
    no_sync_pyproject: bool = Field(
        False, description="Do not sync with pyproject.toml."
    )
    pyproject_file: Path = Field(
        Path("pyproject.toml"), description="pyproject.toml file path."
    )
    no_sync_codemeta: bool = Field(False, description="Do not sync with codemeta.json.")
    codemeta_file: Path = Field(
        Path("codemeta.json"), description="codemeta.json file path."
    )
    show_info: bool = Field(
        False, description="Show basic information messages on run."
    )
    verbose: bool = Field(False, description="Show verbose messages on run.")
    debug: bool = Field(False, description="Show debug messages on run.")


# --------
# Project metadata model (modified from CITATION.cff)


class Person(SomesyBaseModel):
    """A person that is used in project metadata. Required fields are given-names, family-names, and  email."""

    address: Optional[
        Annotated[str, Field(min_length=1, description="The person's address.")]
    ]
    affiliation: Optional[
        Annotated[str, Field(min_length=1, description="The person's affiliation.")]
    ]
    alias: Optional[
        Annotated[str, Field(min_length=1, description="The person's alias.")]
    ]
    city: Optional[
        Annotated[str, Field(min_length=1, description="The person's city.")]
    ]
    country: Optional[Country] = Field(None, description="The person's country.")
    email: Annotated[
        str,
        Field(
            regex=r"^[\S]+@[\S]+\.[\S]{2,}$",
            description="The person's email address.",
        ),
    ]
    family_names: Annotated[
        str,
        Field(
            min_length=1,
            alias="family-names",
            description="The person's family names.",
        ),
    ]
    fax: Optional[
        Annotated[str, Field(min_length=1, description="The person's fax number.")]
    ]
    given_names: Annotated[
        str,
        Field(
            min_length=1,
            alias="given-names",
            description="The person's given names.",
        ),
    ]
    name_particle: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                alias="name-particle",
                description="The person's name particle, e.g., a nobiliary particle or a preposition meaning 'of' or 'from' (for example 'von' in 'Alexander von Humboldt').",
                examples=["von"],
            ),
        ]
    ]
    name_suffix: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                alias="name-suffix",
                description="The person's name-suffix, e.g. 'Jr.' for Sammy Davis Jr. or 'III' for Frank Edwin Wright III.",
                examples=["Jr.", "III"],
            ),
        ]
    ]
    orcid: Optional[AnyUrl] = Field(None, description="The person's ORCID url.")
    post_code: Optional[
        Annotated[
            str,
            Field(
                min_length=1, alias="post-code", description="The person's post-code."
            ),
        ]
    ]
    region: Optional[
        Annotated[str, Field(min_length=1, description="The person's region.")]
    ]
    tel: Optional[
        Annotated[str, Field(min_length=1, description="The person's phone number.")]
    ]
    website: Optional[AnyUrl] = Field(None, description="The person's website.")
    contribution: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                description="Summary of how the person contributed to the project.",
            ),
        ]
    ]
    contribution_type: Optional[
        Union[ContributionTypeEnum, List[ContributionTypeEnum]]
    ] = Field(None, description="Contribution type of contributor.")
    contribution_begin: Optional[date] = Field(
        None, description="Beginning date of the contribution."
    )
    contribution_end: Optional[date] = Field(
        None, description="Ending date of the contribution."
    )

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

        if not names:
            return ""
        return " ".join(names)

    def same_person(self, other) -> bool:
        """Return whether two Person metadata records are about the same real person.

        Uses heuristic match based on orcid, email and name (whichever are provided).
        """
        if self.orcid is not None and other.orcid is not None:
            # having orcids is the best case, a real identifier
            return self.orcid == other.orcid

        # otherwise, try to match according to mail/name
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

    class Config:
        """Pydantic config."""

        extra = Extra.ignore

    @root_validator
    def ensure_distinct_people(cls, values):
        """Make sure that no person is listed twice in the same person list."""
        for key in ["authors", "maintainers", "contributors"]:
            ps = values.get(key)
            if not ps:
                continue
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    if ps[i].same_person(ps[j]):
                        p1 = pretty_repr(json.loads(ps[i].json()))
                        p2 = pretty_repr(json.loads(ps[j].json()))
                        msg = (
                            f"Same person is listed twice in '{key}' list:\n{p1}\n{p2}"
                        )
                        raise ValueError(msg)
        return values

    name: str = Field(description="Package name.")
    description: str = Field(description="Package description.")
    version: Optional[str] = Field(description="Package version.")
    license: LicenseEnum = Field(description="SPDX License string.")
    repository: Optional[AnyUrl] = Field(None, description="URL of the repository.")
    homepage: Optional[AnyUrl] = Field(None, description="URL of the package homepage.")

    keywords: List[str] = Field([], description="Keywords that describe the package.")
    authors: List[Person] = Field(min_items=1, description="Package authors.")
    maintainers: List[Person] = Field([], description="Package maintainers.")
    contributors: List[Person] = Field([], description="Package contributors.")
