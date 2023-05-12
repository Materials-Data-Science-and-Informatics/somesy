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
    # update the keys that has underscores to dashes
    for key in list(cff_dict.keys()):
        if "_" in key:
            cff_dict[key.replace("_", "-")] = cff_dict.pop(key)
    return cff_dict
