"""Pyproject models."""

from typing import Annotated

from packaging.version import parse as parse_version
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from somesy.core.types import HttpUrlStr


class FortranConfig(BaseModel):
    """Fortran configuration model."""

    model_config = {"use_enum_values": True}

    name: Annotated[
        str,
        Field(pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$", description="Package name"),
    ]
    version: Annotated[
        str | None,
        Field(
            pattern=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$",
            description="Package version",
        ),
    ] = None
    description: Annotated[str | None, Field(description="Package description")] = None
    license: Annotated[
        str | None,
        Field(description="SPDX license identifier(s)."),
    ] = None
    author: Annotated[str | None, Field(description="Package author information")] = (
        None
    )
    maintainer: Annotated[
        str | None, Field(description="Package maintainer information")
    ] = None
    copyright: Annotated[str | None, Field(description="Package copyright text")] = None
    homepage: Annotated[HttpUrlStr | None, Field(description="Package homepage")] = None
    keywords: Annotated[
        set[str] | None, Field(description="Keywords that describe the package")
    ] = None
    categories: Annotated[
        set[str] | None, Field(description="Categories that package falls into")
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
