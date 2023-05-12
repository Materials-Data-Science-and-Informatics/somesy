from pathlib import Path

import pytest
from pydantic import AnyUrl
from pydantic.tools import parse_obj_as

from somesy.core.models import Person
from somesy.pyproject.poetry import Poetry


@pytest.fixture
def poetry():
    return Poetry(Path("tests/pyproject/data/pyproject.full.toml"))


def test_name(poetry):
    assert poetry.name == "somesy"
    poetry.name = "new name"
    assert poetry.name == "new name"


def test_version(poetry):
    assert poetry.version == "0.0.1"
    poetry.version = "0.0.2"
    assert poetry.version == "0.0.2"


def test_description(poetry):
    assert (
        poetry.description
        == "A cli tool for synchronizing CITATION.CFF with project files."
    )
    poetry.description = "new description"
    assert poetry.description == "new description"


def test_authors(poetry):
    # check existing authors
    authors = [
        Person(
            **{
                "email": "m.soylu@fz-juelich.de",
                "given-names": "Mustafa",
                "family-names": "Soylu",
            }
        )
    ]
    poetry.authors = authors
    assert set(poetry.authors) == set(["Mustafa Soylu <m.soylu@fz-juelich.de>"])

    # set authors
    new_authors = [
        Person(**{"email": "aaa@aaa.aaa", "given-names": "AA", "family-names": "BB"}),
    ]
    poetry.authors = new_authors
    assert set(poetry.authors) == set(["AA BB <aaa@aaa.aaa>"])


def test_maintainers(poetry):
    # check existing maintainers
    maintainers = [
        Person(
            **{
                "email": "m.soylu@fz-juelich.de",
                "given-names": "Mustafa",
                "family-names": "Soylu",
            }
        )
    ]
    poetry.maintainers = maintainers
    assert set(poetry.maintainers) == set(["Mustafa Soylu <m.soylu@fz-juelich.de>"])

    # set maintainers
    new_maintainers = [
        Person(**{"email": "aaa@aaa.aaa", "given-names": "AA", "family-names": "BB"}),
    ]
    poetry.maintainers = new_maintainers
    assert set(poetry.maintainers) == set(["AA BB <aaa@aaa.aaa>"])


def test_license(poetry):
    # check existing
    assert poetry.license == "MIT"

    # set new
    poetry.license = "GPT-3"
    assert poetry.license == "GPT-3"


def test_keywords(poetry):
    assert poetry.keywords == ["metadata", "rdm", "FAIR", "framework"]
    poetry.keywords = ["keyword1", "keyword2"]
    assert poetry.keywords == ["keyword1", "keyword2"]


def test_homepage(poetry):
    # as string
    assert (
        poetry.homepage
        == "https://github.com/Materials-Data-Science-and-Informatics/somesy"
    )
    poetry.homepage = "https://test.test"
    assert poetry.homepage == "https://test.test"

    # as AnyUrl
    poetry.homepage = parse_obj_as(AnyUrl, "https://test.test2")
    assert poetry.homepage == "https://test.test2"


def test_repository(poetry):
    # as string
    assert (
        poetry.repository
        == "https://github.com/Materials-Data-Science-and-Informatics/somesy"
    )

    poetry.repository = "https://test.test"
    assert poetry.repository == "https://test.test"

    poetry.repository = parse_obj_as(AnyUrl, "https://test.test2")
    assert poetry.repository == "https://test.test2"
