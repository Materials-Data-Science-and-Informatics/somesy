"""package.json validation models."""

import re
from logging import getLogger
from typing import List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing_extensions import Annotated

from somesy.core.types import HttpUrlStr

logger = getLogger("somesy")


class PackageAuthor(BaseModel):
    """Package author model."""

    name: Annotated[Optional[str], Field(description="Author name")]
    email: Annotated[Optional[EmailStr], Field(description="Author email")] = None
    url: Annotated[
        Optional[HttpUrlStr], Field(description="Author website or orcid page")
    ] = None


class PackageRepository(BaseModel):
    """Package repository model."""

    type: Annotated[Optional[str], Field(description="Repository type")] = None
    url: Annotated[str, Field(description="Repository url")]


class PackageLicense(BaseModel):
    """Package license model."""

    type: Annotated[Optional[str], Field(description="License type")] = None
    url: Annotated[str, Field(description="License url")]


NPM_PKG_AUTHOR = r"^(.*?)\s*(?:<([^>]+)>)?\s*(?:\(([^)]+)\))?$"
NPM_PKG_NAME = r"^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$"
NPM_PKG_VERSION = r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*)?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"  # noqa: E501


class PackageJsonConfig(BaseModel):
    """Package.json config model."""

    model_config = dict(populate_by_name=True)

    name: Annotated[str, Field(description="Package name")]
    version: Annotated[str, Field(description="Package version")]
    description: Annotated[Optional[str], Field(description="Package description")] = (
        None
    )
    author: Annotated[
        Optional[Union[str, PackageAuthor]], Field(description="Package author")
    ] = None
    maintainers: Annotated[
        Optional[List[Union[str, PackageAuthor]]],
        Field(description="Package maintainers"),
    ] = None
    contributors: Annotated[
        Optional[List[Union[str, PackageAuthor]]],
        Field(description="Package contributors"),
    ] = None
    license: Annotated[
        Optional[Union[str, PackageLicense]], Field(description="Package license")
    ] = None
    repository: Annotated[
        Optional[Union[PackageRepository, str]], Field(description="Package repository")
    ] = None
    homepage: Annotated[Optional[HttpUrlStr], Field(description="Package homepage")] = (
        None
    )
    keywords: Annotated[
        Optional[List[str]], Field(description="Keywords that describe the package")
    ] = None

    # convert package author to dict if it is a string
    @classmethod
    def convert_author(cls, author: str) -> Optional[PackageAuthor]:
        """Convert author string to PackageAuthor model."""
        # parse author string to "name <email> (url)" format with regex
        author_match = re.match(NPM_PKG_AUTHOR, author)
        if not author_match:
            raise ValueError(f"Invalid author format: {author}")
        author_name = author_match[1]
        author_email = author_match[2]
        author_url = author_match[3]

        if author_email is None:
            return None
        return PackageAuthor(name=author_name, email=author_email, url=author_url)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate package name."""
        if re.match(NPM_PKG_NAME, v) is None:
            raise ValueError("Invalid name")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate package version."""
        if re.match(NPM_PKG_VERSION, v) is None:
            raise ValueError("Invalid version")
        return v

    @field_validator("author")
    @classmethod
    def validate_author(cls, v):
        """Validate package author."""
        return cls.convert_author(v) if isinstance(v, str) else v

    @field_validator("maintainers", "contributors")
    @classmethod
    def validate_people(cls, v):
        """Validate package maintainers and contributors."""
        people = []
        for p in v:
            if isinstance(p, str):
                author = cls.convert_author(p)
                if author is not None:
                    people.append(cls.convert_author(p))
                else:
                    logger.warning(
                        f"Invalid email format for maintainer/contributor {p}, omitting."
                    )
            elif p.email is not None:
                people.append(p)
            else:
                logger.warning(
                    f"Invalid email format for maintainer/contributor {p}, omitting."
                )
        return people
