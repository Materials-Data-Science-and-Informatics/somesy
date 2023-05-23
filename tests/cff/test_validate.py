import pytest

from somesy.cff.validate import validate_citation


@pytest.fixture
def cff_path():
    return "tests/cff/data/CITATION.cff"


@pytest.fixture
def cff_reject_path():
    return "tests/cff/data/reject.cff"


def test_validate_citation(cff_path):
    validate_citation(cff_path)


def test_validate_citation_none():
    with pytest.raises(ValueError):
        validate_citation(None)


def test_validate_citation_reject(cff_reject_path):
    with pytest.raises(ValueError):
        validate_citation(cff_reject_path)
