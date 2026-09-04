"""Pyproject models."""

import re
from pathlib import Path
from typing import Annotated

from packaging.version import parse as parse_version
from pydantic import BaseModel, Field, field_validator, model_validator

from somesy.core.types import HttpUrlStr


class RustConfig(BaseModel):
    """Rust configuration model."""

    model_config = {"use_enum_values": True}

    name: Annotated[
        str,
        Field(
            pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$",
            max_length=64,
            description="Package name",
        ),
    ]
    version: Annotated[
        str,
        Field(
            pattern=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$",
            description="Package version",
        ),
    ]
    description: Annotated[str | None, Field(description="Package description")] = None
    license: Annotated[
        str | None,
        Field(
            description="A combination SPDX license identifiers with AND, OR and so on."
        ),
    ] = None
    authors: Annotated[set[str], Field(description="Package authors")]
    maintainers: Annotated[
        set[str] | None, Field(description="Package maintainers")
    ] = None
    readme: Annotated[
        Path | list[Path] | None, Field(description="Package readme file(s)")
    ] = None
    license_file: Annotated[Path | None, Field(description="Package license file")] = (
        None
    )
    homepage: Annotated[HttpUrlStr | None, Field(description="Package homepage")] = None
    repository: Annotated[
        HttpUrlStr | None, Field(description="Package repository")
    ] = None
    documentation: Annotated[
        HttpUrlStr | None, Field(description="Package documentation page")
    ] = None
    keywords: Annotated[
        set[str] | None, Field(description="Keywords that describe the package")
    ] = None
    classifiers: Annotated[list[str] | None, Field(description="pypi classifiers")] = (
        None
    )
    urls: Annotated[dict[str, HttpUrlStr] | None, Field(description="Package URLs")] = (
        None
    )

    @model_validator(mode="before")
    @classmethod
    def license_or_file(cls, values):
        """License and license file are mutually exclusive."""
        if "license" in values and "license_file" in values:
            raise ValueError("license and license_file are mutually exclusive")
        return values

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError as err:
            raise ValueError("Invalid version") from err
        return v

    @field_validator("readme", "license_file")
    @classmethod
    def validate_readme(cls, v):
        """Validate readme file(s) by checking whether files exist."""
        if isinstance(v, list):
            if any(not e.is_file() for e in v):
                raise ValueError("Some file(s) do not exist")
        else:
            if not v.is_file():
                raise ValueError("File does not exist")

    @field_validator("keywords")
    @classmethod
    def check_keywords_field(cls, v):
        """Check the keywords field."""
        if v is None:
            return v

        # Check if number of keywords is at most 5
        if len(v) > 5:
            raise ValueError("A maximum of 5 keywords is allowed")

        for keyword in v or []:
            check_keyword(keyword)

        return v


def check_keyword(keyword: str):
    """Check if keyword is valid."""
    # Check if keyword is ASCII and has at most 20 characters
    if not keyword.isascii() or len(keyword) > 20:
        raise ValueError(
            "Each keyword must be ASCII text and have at most 20 characters"
        )

    # Check if keyword starts with an alphanumeric character
    if not re.match(r"^[a-zA-Z0-9]", keyword):
        raise ValueError("Each keyword must start with an alphanumeric character")

    # Check if keyword contains only allowed characters
    if not re.match(r"^[a-zA-Z0-9_\-+]+$", keyword):
        raise ValueError("Keywords can only contain letters, numbers, _, -, or +")
