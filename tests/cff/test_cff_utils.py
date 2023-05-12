import pytest

from somesy.cff.utils import person_to_cff_dict
from somesy.core.models import Person


@pytest.fixture
def person():
    p = {
        "given-names": "John",
        "family-names": "Doe",
        "email": "test@test.test",
    }
    return Person(**p)


def test_person_to_cff_dict(person):
    cff_dict = person_to_cff_dict(person)
    assert cff_dict == {
        "given-names": "John",
        "family-names": "Doe",
        "email": "test@test.test",
    }
