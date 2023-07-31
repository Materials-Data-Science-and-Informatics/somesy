"""package.json validation models."""
import re
from typing import List, Optional, Union

from pydantic import AnyUrl, BaseModel, EmailStr, ValidationError, validator


class PackageAuthor(BaseModel):
    """Package author model."""

    name: Optional[str]
    email: Optional[EmailStr]
    url: Optional[AnyUrl]


class PackageRepository(BaseModel):
    """Package repository model."""

    type: str
    url: Optional[str]


class PackageLicense(BaseModel):
    """Package license model."""

    type: str
    url: Optional[str]


class PackageJsonConfig(BaseModel):
    """Package.json config model."""

    name: str
    version: str
    description: Optional[str]
    author: Optional[Union[str, PackageAuthor]]
    maintainers: Optional[List[Union[str, PackageAuthor]]]
    contributors: Optional[List[Union[str, PackageAuthor]]]
    license: Optional[Union[str, PackageLicense]]
    repository: Optional[PackageRepository]
    homepage: Optional[AnyUrl]
    keywords: Optional[List[str]]

    # convert package author to dict if it is a string
    @classmethod
    def convert_author(cls, author: str) -> PackageAuthor:
        """Convert author string to PackageAuthor model."""
        # parse author string to "name <email> (url)" format with regex
        author_regex = r"^(.*?)\s*(?:<([^>]+)>)?\s*(?:\(([^)]+)\))?$"
        author_match = re.match(author_regex, author)
        if not author_match:
            raise ValidationError(f"Invalid author format: {author}")
        author_name = author_match[1]
        author_email = author_match[2]
        author_url = author_match[3]

        return PackageAuthor(name=author_name, email=author_email, url=author_url)

    @validator("name")
    def validate_name(cls, v):
        """Validate package name."""
        pattern = r"^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$"
        if re.match(pattern, v) is None:
            raise ValidationError("Invalid name")

        return v

    @validator("version")
    def validate_version(cls, v):
        """Validate package version."""
        # pattern for npm version
        pattern = r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*)?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        if re.match(pattern, v) is None:
            raise ValidationError("Invalid version")
        return v

    @validator("author")
    def validate_author(cls, v):
        """Validate package author."""
        return cls.convert_author(v) if isinstance(v, str) else v

    @validator("maintainers", "contributors")
    def validate_people(cls, v):
        """Validate package maintainers and contributors."""
        people = []
        for p in v:
            if isinstance(p, str):
                people.append(cls.convert_author(p))
            else:
                people.append(p)
        return people

    class Config:
        """Pydantic config."""

        allow_population_by_field_name = True
