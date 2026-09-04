"""Merge harvested metadata into the canonical Somesy project model."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from typing import Any

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.git.models import GitAuthor, GitMetadata

logger = logging.getLogger("somesy")

_SCALAR_FIELDS = (
    "name",
    "version",
    "description",
    "license",
    "homepage",
    "repository",
    "documentation",
)


def _value(value: Any) -> Any:
    """Convert common endpoint wrapper values to project-model values."""
    if hasattr(value, "text"):
        return value.text
    if isinstance(value, (set, tuple)):
        return list(value)
    if isinstance(value, list):
        return [_value(item) for item in value]
    return getattr(value, "value", value)


def _repository(value: Any) -> str | None:
    """Return a repository URL acceptable to ProjectMetadata when possible."""
    value = _value(value)
    if not isinstance(value, str):
        return None
    if match := re.fullmatch(r"git@([^:]+):(.+)", value):
        return f"https://{match[1]}/{match[2]}"
    if value.startswith("ssh://git@"):
        return "https://" + value.removeprefix("ssh://git@")
    return value


def _merge_person(existing: Person | Entity, incoming: Person | Entity):
    """Fill missing fields and combine roles for one matching person."""
    updates: dict[str, Any] = {}
    for field in type(existing).model_fields:
        old = getattr(existing, field)
        new = getattr(incoming, field)
        if field == "contribution_types":
            values = list(dict.fromkeys((old or []) + (new or [])))
            if values != (old or []):
                updates[field] = values
        elif field in {"author", "maintainer"}:
            if new and not old:
                updates[field] = True
        elif field == "publication_author":
            if new is True and old is not True:
                updates[field] = True
            elif old is None and new is not None:
                updates[field] = new
        elif old in (None, "") and new not in (None, ""):
            updates[field] = new
    return existing.model_copy(update=updates) if updates else existing


def _merge_people(
    existing: list[Person | Entity], incoming: Iterable[Person | Entity]
) -> list[Person | Entity]:
    """Merge people using the model's existing identity heuristics."""
    result = list(existing)
    for candidate in incoming:
        for index, person in enumerate(result):
            same_person = (
                isinstance(person, Person)
                and isinstance(candidate, Person)
                and person.same_person(candidate)
            )
            same_entity = (
                isinstance(person, Entity)
                and isinstance(candidate, Entity)
                and person.same_person(candidate)
            )
            if same_person or same_entity:
                result[index] = _merge_person(person, candidate)
                break
        else:
            result.append(candidate)
    return result


def _git_person(author: GitAuthor) -> Person | None:
    """Convert a Git author into a Somesy Person."""
    identity = author.name
    if author.email:
        identity = f"{identity} <{author.email}>"
    try:
        return Person.from_name_email_string(identity).model_copy(
            update={
                "author": author.author,
                "contribution_types": author.contribution_types,
            }
        )
    except (IndexError, ValueError):
        logger.warning("Cannot convert Git author '%s' to Somesy metadata.", identity)
        return None


def merge_metadata(
    sources: Iterable[dict[str, Any]], git: GitMetadata | None = None
) -> ProjectMetadata:
    """Merge harvested endpoint data and Git data into ProjectMetadata."""
    data: dict[str, Any] = {"people": [], "entities": []}
    keywords: list[str] = []

    candidates = list(sources)
    if git is not None:
        candidates.append(git.model_dump(exclude_none=True))

    for source in candidates:
        for field in _SCALAR_FIELDS:
            value = source.get(field)
            if field == "repository":
                value = _repository(value)
            else:
                value = _value(value)
            if value not in (None, "") and field not in data:
                data[field] = value

        for keyword in _value(source.get("keywords", [])) or []:
            if keyword not in keywords:
                keywords.append(keyword)

        people = source.get("people", []) or []
        entities = source.get("entities", []) or []
        data["people"] = _merge_people(data["people"], people)
        data["entities"] = _merge_people(data["entities"], entities)

        for author in source.get("authors", []) or []:
            if isinstance(author, dict):
                author = GitAuthor(**author)
            if person := _git_person(author):
                data["people"] = _merge_people(data["people"], [person])

    if keywords:
        data["keywords"] = keywords
    return ProjectMetadata(**data)
