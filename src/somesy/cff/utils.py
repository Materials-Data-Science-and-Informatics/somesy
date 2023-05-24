"""Utility functions for cff module."""
from json import loads

from somesy.core.models import Person


def person_to_cff_dict(person: Person) -> dict:
    """Convert project metadata person object to cff dict for person format."""
    cff_dict = loads(
        person.json(
            by_alias=True,
            exclude_none=True,
            exclude={
                "contribution",
                "contribution_type",
                "contribution_begin",
                "contribution_end",
            },
            exclude_unset=True,
        )
    )
    return cff_dict
