"""Pyproject models."""

from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import Annotated

from packaging.version import parse as parse_version
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

from somesy.core.models import LicenseEnum
from somesy.core.types import HttpUrlStr

EMailAddress = TypeAdapter(EmailStr)
logger = getLogger("somesy")


class STPerson(BaseModel):
    """Person model for setuptools."""

    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str | None, Field(min_length=1)] = None

    def __str__(self):
        """Return string representation of STPerson."""
        if self.email:
            return f"{self.name} <{self.email}>"
        else:
            return self.name


class License(BaseModel):
    """License model for setuptools."""

    model_config = {"validate_assignment": True}

    file: Path | None = None
    text: LicenseEnum | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_xor(cls, values):
        """Validate that only one of file or text is set."""
        # check if this has just str or list of str
        if isinstance(values, str):
            if values in LicenseEnum.__members__:
                return {"text": values}
            else:
                raise ValueError("Invalid license.")
        if isinstance(values, list):
            # check if all elements are valid string for LicenseEnum
            for v in values:
                if not isinstance(v, str):
                    raise TypeError("All elements must be strings.")
                if v not in LicenseEnum.__members__:
                    raise ValueError("Invalid license.")
            return values
        if sum([bool(v) for v in values.values()]) != 1:
            raise ValueError("Either file or text must be set.")
        return values


class PoetryConfig(BaseModel):
    """Poetry configuration model."""

    model_config = {"use_enum_values": True}

    name: Annotated[
        str,
        Field(pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$", description="Package name"),
    ]
    version: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$",
            description="Package version",
        ),
    ]
    description: Annotated[
        str | None, Field(default=None, description="Package description")
    ]
    dynamic: Annotated[
        list[str] | None, Field(default=None, description="PEP 621 dynamic fields")
    ]

    @model_validator(mode="after")
    def validate_required_unless_dynamic(self):
        """Validate that version and description are present unless listed in dynamic."""
        dynamic = self.dynamic or []
        if self.version is None and "version" not in dynamic:
            raise ValueError(
                "Field 'version' is required when not listed in 'dynamic'."
            )
        if self.description is None and "description" not in dynamic:
            raise ValueError(
                "Field 'description' is required when not listed in 'dynamic'."
            )
        return self

    license: Annotated[
        LicenseEnum | list[LicenseEnum] | License | str | None,
        Field(description="An SPDX license identifier."),
    ]

    # v1 has str, v2 has STPerson
    authors: Annotated[list[str | STPerson], Field(description="Package authors")]
    maintainers: Annotated[
        list[str | STPerson] | None, Field(description="Package maintainers")
    ] = None

    readme: Annotated[
        Path | list[Path] | None, Field(description="Package readme file(s)")
    ] = None
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

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError as err:
            raise ValueError("Invalid version") from err
        return v

    @field_validator("authors", "maintainers")
    @classmethod
    def validate_email_format(cls, v):
        """Validate person format, omit person that is not in correct format, don't raise an error."""
        if v is None:
            return []
        validated = []
        seen = set()
        for author in v:
            if isinstance(author, STPerson) and author.email:
                if not EMailAddress.validate_python(author.email):
                    logger.warning(
                        f"Invalid email format for author/maintainer {author}."
                    )
                else:
                    author_str = str(author)
                    if author_str not in seen:
                        seen.add(author_str)
                        validated.append(author)
                    else:
                        logger.warning(f"Same person {author} is added multiple times.")
            elif (
                isinstance(author, str)
                and "@" in author
                and EMailAddress.validate_python(author.split(" ")[-1][1:-1])
            ):
                validated.append(author)
            else:
                author_str = str(author)
                if author_str not in seen:
                    seen.add(author_str)
                    validated.append(author)
                else:
                    logger.warning(f"Same person {author} is added multiple times.")

        return validated

    @field_validator("readme")
    @classmethod
    def validate_readme(cls, v):
        """Validate readme file(s) by checking whether files exist."""
        if isinstance(v, list):
            if any(not e.is_file() for e in v):
                logger.warning("Some readme file(s) do not exist")
        else:
            if not v.is_file():
                logger.warning("Readme file does not exist")


class ContentTypeEnum(Enum):
    """Content type enum for setuptools field file."""

    plain = "text/plain"
    rst = "text/x-rst"
    markdown = "text/markdown"


class File(BaseModel):
    """File model for setuptools."""

    file: Path
    content_type: ContentTypeEnum | None = Field(alias="content-type")


class URLs(BaseModel):
    """URLs model for setuptools."""

    homepage: HttpUrlStr | None = None
    repository: HttpUrlStr | None = None
    documentation: HttpUrlStr | None = None
    changelog: HttpUrlStr | None = None


class SetuptoolsConfig(BaseModel):
    """Setuptools input model. Required fields are name, version, description, and requires_python."""

    model_config = {"use_enum_values": True}

    name: Annotated[str, Field(pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$")]
    version: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$",
        ),
    ]
    description: str | None = None
    dynamic: Annotated[
        list[str] | None, Field(default=None, description="PEP 621 dynamic fields")
    ]

    @model_validator(mode="after")
    def validate_required_unless_dynamic(self):
        """Validate that version and description are present unless listed in dynamic."""
        dynamic = self.dynamic or []
        if self.version is None and "version" not in dynamic:
            raise ValueError(
                "Field 'version' is required when not listed in 'dynamic'."
            )
        if self.description is None and "description" not in dynamic:
            raise ValueError(
                "Field 'description' is required when not listed in 'dynamic'."
            )
        return self

    readme: Path | list[Path] | File | None = None
    license: License | LicenseEnum | str | None = Field(
        None, description="An SPDX license identifier."
    )
    authors: list[STPerson] | None = None
    maintainers: list[STPerson] | None = None
    keywords: set[str] | None = None
    classifiers: list[str] | None = None
    urls: URLs | None = None

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError as err:
            raise ValueError("Invalid version") from err
        return v

    @field_validator("readme")
    @classmethod
    def validate_readme(cls, v):
        """Validate readme file(s) by checking whether files exist."""
        if isinstance(v, list):
            if any(not e.is_file() for e in v):
                raise ValueError("Some file(s) do not exist")
        elif type(v) is File:
            if not Path(v.file).is_file():
                raise ValueError("File does not exist")
        else:
            if not v.is_file():
                raise ValueError("File does not exist")

    @field_validator("authors", "maintainers")
    @classmethod
    def validate_email_format(cls, v):
        """Validate email format."""
        for person in v:
            if person.email and not EMailAddress.validate_python(person.email):
                raise ValueError("Invalid email format")
        return v
