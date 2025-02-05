"""Pyproject models."""

from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)
from typing_extensions import Annotated

from somesy.core.types import HttpUrlStr


class MkDocsConfig(BaseModel):
    """MkDocs configuration model."""

    model_config = dict(use_enum_values=True)

    site_name: Annotated[
        str,
        Field(pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$", description="Site name"),
    ]
    site_description: Annotated[
        Optional[str], Field(description="Site description")
    ] = None
    site_author: Annotated[Optional[str], Field(description="Site authors")] = None
    site_url: Annotated[Optional[HttpUrlStr], Field(description="Site homepage")] = None
    repo_url: Annotated[
        Optional[HttpUrlStr], Field(description="Package repository")
    ] = None
    repo_name: Annotated[Optional[str], Field(description="Repository name")] = None
