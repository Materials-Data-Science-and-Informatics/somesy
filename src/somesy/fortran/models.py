"""Pyproject models."""

from typing import Optional, Set

from packaging.version import parse as parse_version
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
from typing_extensions import Annotated

from somesy.core.types import HttpUrlStr


class FortranConfig(BaseModel):
    """Fortran configuration model."""

    model_config = dict(use_enum_values=True)

    name: Annotated[
        str,
        Field(pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$", description="Package name"),
    ]
    version: Annotated[
        Optional[str],
        Field(
            pattern=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$",
            description="Package version",
        ),
    ] = None
    description: Annotated[Optional[str], Field(description="Package description")] = (
        None
    )
    license: Annotated[
        Optional[str],
        Field(description="SPDX license identifier(s)."),
    ] = None
    author: Annotated[
        Optional[str], Field(description="Package author information")
    ] = None
    maintainer: Annotated[
        Optional[str], Field(description="Package maintainer information")
    ] = None
    copyright: Annotated[Optional[str], Field(description="Package copyright text")] = (
        None
    )
    homepage: Annotated[Optional[HttpUrlStr], Field(description="Package homepage")] = (
        None
    )
    keywords: Annotated[
        Optional[Set[str]], Field(description="Keywords that describe the package")
    ] = None
    categories: Annotated[
        Optional[Set[str]], Field(description="Categories that package falls into")
    ] = None

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError as err:
            raise ValueError("Invalid version") from err
        return v
