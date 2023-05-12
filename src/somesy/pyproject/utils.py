"""Utility functions for pyproject.toml generation."""
from somesy.core.models import Person


def person_to_poetry_string(person: Person):
    """Convert project metadata person object to poetry string for person format "full name <email>."""
    return f"{person.full_name} <{person.email}>"


def person_to_setuptools_dict(person: Person):
    """Convert project metadata person object to setuptools dict for person format."""
    return {"name": person.full_name, "email": person.email}
