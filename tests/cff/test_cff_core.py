from pathlib import Path

import pytest

from somesy.cff.core import CFF
from somesy.core.core import get_project_metadata
from somesy.core.models import Person


@pytest.fixture
def cff():
    return CFF(Path("tests/cff/data/CITATION.cff"))


@pytest.fixture
def people():
    people = {
        "family-names": "Soylu",
        "given-names": "Mustafa",
        "email": "m.soylu@fz-juelich.de",
        "orcid": "https://orcid.org/0000-0003-2637-0432",
    }
    return [Person(**people)]


@pytest.fixture
def project_metadata():
    return get_project_metadata(Path("tests/cff/data/pyproject.base.toml"))


def test_version(cff):
    # test existing version
    assert cff.version == "0.0.1"

    # empty entry
    cff.version = None
    assert cff.version == "0.0.1"

    # new version
    new_version = "0.2.0"
    cff.version = new_version
    assert cff.version == new_version


def test_description(cff: CFF):
    # test existing description
    assert (
        cff.description
        == "A cli tool for synchronizing CITATION.CFF with project files."
    )

    # empty entry
    cff.description = None
    assert (
        cff.description
        == "A cli tool for synchronizing CITATION.CFF with project files."
    )

    # new description
    new_description = "new description"
    cff.description = new_description
    assert cff.description == new_description


def test_keywords(cff):
    # test existing keywords
    assert cff.keywords == ["metadata", "rdm", "standards", "FAIR", "python3"]

    # empty entry
    cff.keywords = None
    assert cff.keywords == ["metadata", "rdm", "standards", "FAIR", "python3"]

    # new keywords
    new_keywords = ["new keyword"]
    cff.keywords = new_keywords
    assert cff.keywords == new_keywords


def test_license(cff):
    # test existing license
    assert cff.license == "MIT"

    # empty entry
    cff.license = None
    assert cff.license == "MIT"

    # new license
    new_license = "GPT-3"
    cff.license = new_license
    assert cff.license == new_license


def test_repository(cff):
    # test existing repository
    assert (
        cff.repository
        == "https://github.com/Materials-Data-Science-and-Informatics/somesy"
    )

    # empty entry
    cff.repository = None
    assert (
        cff.repository
        == "https://github.com/Materials-Data-Science-and-Informatics/somesy"
    )

    # new repository
    new_repository = "https://test.test"
    cff.repository = new_repository
    assert cff.repository == new_repository


def test_homepage(cff):
    # test existing homepage
    assert (
        cff.homepage
        == "https://github.com/Materials-Data-Science-and-Informatics/somesy"
    )

    # empty entry
    cff.homepage = None
    assert (
        cff.homepage
        == "https://github.com/Materials-Data-Science-and-Informatics/somesy"
    )

    # new homepage
    new_homepage = "https://test.test"
    cff.homepage = new_homepage
    assert cff.homepage == new_homepage


def test_sync(cff, project_metadata):
    cff.sync(project_metadata)
    assert cff.version == "0.1.0"
