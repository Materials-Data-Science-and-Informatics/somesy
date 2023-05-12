import pytest

from somesy.cff.validate import validate_citation


@pytest.fixture
def cff_path():
    return "tests/cff/data/CITATION.cff"


@pytest.fixture
def cff_reject_path():
    return "tests/cff/data/reject.cff"


def test_validate_citation(cff_path):
    assert validate_citation(cff_path) == True


def test_validate_citation_none():
    assert validate_citation(None) == False


def test_validate_citation_reject(cff_reject_path):
    assert validate_citation(cff_reject_path) == False
