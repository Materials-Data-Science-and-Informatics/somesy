"""Julia model."""

import uuid
from logging import getLogger
from typing import Optional, Set

from packaging.version import parse as parse_version
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)
from typing_extensions import Annotated

EMailAddress = TypeAdapter(EmailStr)
logger = getLogger("somesy")


class JuliaConfig(BaseModel):
    """Julia configuration model."""

    model_config = dict(use_enum_values=True)

    name: Annotated[
        str,
        Field(description="Package name"),
    ]
    version: Annotated[
        str,
        Field(
            pattern=r"^\d+(\.\d+)*((a|b|rc)\d+)?(post\d+)?(dev\d+)?$",
            description="Package version",
        ),
    ]
    uuid: Annotated[str, Field(description="Package UUID")]
    authors: Annotated[Optional[Set[str]], Field(description="Package authors")] = None

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version using PEP 440."""
        try:
            _ = parse_version(v)
        except ValueError as err:
            raise ValueError("Invalid version") from err
        return v

    @field_validator("authors")
    @classmethod
    def validate_email_format(cls, v):
        """Validate person format, omit person that is not in correct format, don't raise an error."""
        if v is None:
            return []
        validated = []
        for author in v:
            try:
                if not (
                    not isinstance(author, str)
                    or " " not in author
                    or not EMailAddress.validate_python(author.split(" ")[-1][1:-1])
                ):
                    validated.append(author)
                else:
                    logger.warning(
                        f"Invalid email format for author {author}, omitting."
                    )
            except ValidationError:
                logger.warning(f"Invalid format for author {author}, omitting.")
        return validated

    @field_validator("uuid")
    @classmethod
    def validate_uuid(cls, v):
        """Validate uuid field."""
        try:
            _ = uuid.UUID(v)
        except ValueError as err:
            raise ValueError("Invalid UUID") from err
        return v
