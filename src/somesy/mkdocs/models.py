"""Pyproject models."""

from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
)

from somesy.core.types import HttpUrlStr


class MkDocsConfig(BaseModel):
    """MkDocs configuration model."""

    model_config = {"use_enum_values": True}

    site_name: Annotated[
        str,
        Field(pattern=r"^[A-Za-z0-9]+([_-][A-Za-z0-9]+)*$", description="Site name"),
    ]
    site_description: Annotated[str | None, Field(description="Site description")] = (
        None
    )
    site_author: Annotated[str | None, Field(description="Site authors")] = None
    site_url: Annotated[HttpUrlStr | None, Field(description="Site homepage")] = None
    repo_url: Annotated[HttpUrlStr | None, Field(description="Package repository")] = (
        None
    )
    repo_name: Annotated[str | None, Field(description="Repository name")] = None
