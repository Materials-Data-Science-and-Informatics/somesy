"""Pyproject models."""
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from packaging.version import parse as parse_version
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    ValidationError,
    root_validator,
    validator,
)
from typing_extensions import Annotated

from somesy.core.models import LicenseEnum


class PoetryConfig(BaseModel):
    """Poetry configuration model."""

    name: Annotated[str, Field(regex=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$")]
    version: Annotated[
        str, Field(regex=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$")
    ]
    description: str
    license: Optional[Union[LicenseEnum, List[LicenseEnum]]] = Field(
        None, description="An SPDX license identifier."
    )
    authors: Set[str]
    maintainers: Optional[Set[str]] = None
    readme: Optional[Union[Path, List[Path]]] = None
    homepage: Optional[HttpUrl] = None
    repository: Optional[HttpUrl] = None
    documentation: Optional[HttpUrl] = None
    keywords: Optional[Set[str]] = None
    classifiers: Optional[List[str]] = None
    packages: Optional[Dict[str, str]] = None
    dependencies: Optional[
        Dict[str, Union[str, Dict[str, Union[str, List[str]]]]]
    ] = None
    dev_dependencies: Optional[
        Dict[str, Union[str, Dict[str, Union[str, List[str]]]]]
    ] = None
    scripts: Optional[Dict[str, Union[str, Dict[str, Union[str, List[str]]]]]] = None
    extras: Optional[Dict[str, List[str]]] = None
    plugins: Optional[Dict[str, str]] = None
    urls: Optional[Dict[str, HttpUrl]] = None

    @validator("version")
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError:
            raise ValidationError("Invalid version")
        return v

    @validator("authors", "maintainers")
    def validate_email_format(cls, v):
        """Validate email format."""
        for author in v:
            if (
                not isinstance(author, str)
                or " " not in author
                or not EmailStr.validate(author.split(" ")[-1][1:-1])
            ):
                raise ValidationError("Invalid email format")
        return v

    @validator("readme")
    def validate_readme(cls, v):
        """Validate readme file(s) by checking whether files exist."""
        if type(v) is list:
            if any(not e.exists() for e in v):
                raise ValidationError("Some file(s) do not exist")
        else:
            if not v.exists():
                raise ValidationError("File does not exist")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class ContentTypeEnum(Enum):
    """Content type enum for setuptools field file."""

    plain = "text/plain"
    rst = "text/x-rst"
    markdown = "text/markdown"


class File(BaseModel):
    """File model for setuptools."""

    file: Path
    content_type: Optional[ContentTypeEnum] = Field(alias="content-type")


class License(BaseModel):
    """License model for setuptools."""

    file: Optional[Path]
    text: Optional[LicenseEnum]

    class Config:
        """Pydantic configuration."""

        validate_assignment = True

    @root_validator(pre=True)
    def validate_xor(cls, values):
        """Validate that only one of file or text is set."""
        if sum([bool(v) for v in values.values()]) != 1:
            raise ValueError("Either file or text must be set.")
        return values


class STPerson(BaseModel):
    """Person model for setuptools."""

    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str, Field(min_length=1)]


class URLs(BaseModel):
    """URLs model for setuptools."""

    homepage: Optional[HttpUrl] = None
    repository: Optional[HttpUrl] = None
    documentation: Optional[HttpUrl] = None
    changelog: Optional[HttpUrl] = None


class SetuptoolsConfig(BaseModel):
    """Setuptools input model. Required fields are name, version, description, and requires_python."""

    name: Annotated[str, Field(regex=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$")]
    version: Annotated[
        str, Field(regex=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$")
    ]
    description: str
    readme: Optional[Union[Path, List[Path], File]] = None
    requires_python: Annotated[str, Field(alias="requires-python")]
    license: Optional[Union[LicenseEnum, List[LicenseEnum]]] = Field(
        None, description="An SPDX license identifier."
    )
    authors: Optional[List[STPerson]]
    maintainers: Optional[List[STPerson]]
    keywords: Optional[Set[str]]
    classifiers: Optional[List[str]]
    urls: Optional[URLs]

    @validator("version")
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError:
            raise ValidationError("Invalid version")
        return v

    @validator("readme")
    def validate_readme(cls, v):
        """Validate readme file(s) by checking whether files exist."""
        if type(v) is list:
            if any(not e.exists() for e in v):
                raise ValidationError("Some file(s) do not exist")
        elif type(v) is File:
            if not Path(v.file).exists():
                raise ValidationError("File does not exist")
        else:
            if not v.exists():
                raise ValidationError("File does not exist")

    @validator("authors", "maintainers")
    def validate_email_format(cls, v):
        """Validate email format."""
        for person in v:
            if person.email:
                if not EmailStr.validate(person.email):
                    raise ValidationError("Invalid email format")
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
