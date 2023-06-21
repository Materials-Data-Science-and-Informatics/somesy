import pytest

from somesy.core.models import Person
from somesy.pyproject.poetry import Poetry
from somesy.pyproject.setuptools import SetupTools


@pytest.fixture
def person():
    p = {
        "given-names": "John",
        "family-names": "Doe",
        "email": "test@test.test",
    }
    return Person(**p)


def test_person_to_poetry_string(person):
    poetry_string = Poetry._from_person(person)
    assert poetry_string == "John Doe <test@test.test>"


def test_person_to_setuptools_dict(person):
    setuptools_dict = SetupTools._from_person(person)
    assert setuptools_dict == {
        "name": "John Doe",
        "email": "test@test.test",
    }
