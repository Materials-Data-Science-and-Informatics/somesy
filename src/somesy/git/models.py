"""Models for metadata harvested from Git."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import Field

from somesy.core.models import SomesyBaseModel
from somesy.core.types import ContributionTypeEnum


class GitAuthor(SomesyBaseModel):
    """A Git author mapped to a Somesy project contributor."""

    name: str
    email: str | None = None
    commit_count: Annotated[int, Field(ge=0)] = 0
    author: bool = True
    contribution_types: list[ContributionTypeEnum] = Field(
        default_factory=lambda: [ContributionTypeEnum.code], min_length=1
    )


class GitMetadata(SomesyBaseModel):
    """Git values that map to Somesy project metadata."""

    name: str | None = None
    repository: str | None = None
    version: str | None = None
    date_created: date | None = None
    date_modified: date | None = None
    authors: list[GitAuthor] = Field(default_factory=list)
