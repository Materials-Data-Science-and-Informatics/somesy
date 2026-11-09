"""Dynamic fields, license handling, Poetry 2 legacy metadata and URL key spelling."""

import logging

import pytest
import tomlkit

from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.pyproject.writer import Poetry, Pyproject

HEAD = '[project]\nname = "test-pkg"\n'
BUILD = (
    '\n[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n'
)


@pytest.fixture
def metadata() -> ProjectMetadata:
    return ProjectMetadata(
        name="test-pkg",
        description="New description",
        license=LicenseEnum.MIT,
        version="2.0.0",
        keywords=["new", "words"],
        homepage="https://example.com/new",
        repository="https://example.com/new-repo",
        documentation="https://example.com/new-docs",
        people=[
            Person(
                given_names="Jane",
                family_names="Roe",
                email="jane@example.com",
                author=True,
                maintainer=True,
            )
        ],
    )


def write(tmp_path, text):
    path = tmp_path / "pyproject.toml"
    path.write_text(text)
    return path


def sync(path, metadata):
    pyproject = Pyproject(path)
    pyproject.sync(metadata)
    pyproject.save()
    return tomlkit.parse(path.read_text())


# ---- B1 dynamic ----

DYNAMIC_FIELDS = [
    "description",
    "version",
    "license",
    "authors",
    "maintainers",
    "keywords",
    "urls",
]


@pytest.mark.parametrize("field", DYNAMIC_FIELDS)
@pytest.mark.parametrize("poetry", [False, True], ids=["pep621", "poetry2"])
def test_dynamic_field_is_not_written(tmp_path, metadata, caplog, field, poetry):
    build = (
        '\n[build-system]\nrequires = ["poetry-core"]\n'
        'build-backend = "poetry.core.masonry.api"\n'
        if poetry
        else BUILD
    )
    body = ""
    if field != "version":
        body += 'version = "1.0.0"\n'
    if field != "description":
        body += 'description = "Old"\n'
    if poetry and field != "authors":
        body += 'authors = [{ name = "Old", email = "old@example.com" }]\n'
    path = write(tmp_path, HEAD + body + f'dynamic = ["{field}"]\n' + build)

    with caplog.at_level(logging.WARNING, logger="somesy"):
        doc = sync(path, metadata)

    project = doc["project"]
    assert field not in project
    assert f"'{field}' is listed as dynamic" in caplog.text


# ---- B3 license ----


@pytest.mark.parametrize(
    "license_line",
    [
        'license = { file = "LICENSE" }\n',
        'license = "Apache-2.0"\nlicense-files = ["LICENSE*"]\n',
        'license-files = ["LICENSE*"]\n',
    ],
)
def test_existing_license_table_or_license_files_are_kept(
    tmp_path, metadata, caplog, license_line
):
    path = write(
        tmp_path,
        HEAD + 'version = "1.0.0"\ndescription = "Old"\n' + license_line + BUILD,
    )
    before = tomlkit.parse(path.read_text())["project"]

    with caplog.at_level(logging.WARNING, logger="somesy"):
        doc = sync(path, metadata)

    after = doc["project"]
    assert after.get("license") == before.get("license")
    assert after.get("license-files") == before.get("license-files")
    assert "license" in caplog.text and "kept" in caplog.text


def test_license_text_table_is_replaced_by_spdx_expression(tmp_path, metadata, caplog):
    path = write(
        tmp_path,
        HEAD
        + 'version = "1.0.0"\ndescription = "Old"\n'
        + 'license = { text = "Apache-2.0" }\n'
        + BUILD,
    )

    with caplog.at_level(logging.WARNING, logger="somesy"):
        doc = sync(path, metadata)

    assert doc["project"]["license"] == "MIT"
    assert "kept" not in caplog.text


def test_license_string_is_still_updated(tmp_path, metadata):
    path = write(
        tmp_path,
        HEAD
        + 'version = "1.0.0"\ndescription = "Old"\nlicense = "Apache-2.0"\n'
        + BUILD,
    )
    assert sync(path, metadata)["project"]["license"] == "MIT"


# ---- B4 poetry 2 with legacy [tool.poetry] metadata ----

POETRY2 = """\
[project]
name = "test-pkg"
version = "1.0.0"
description = "Old"
license = "Apache-2.0"
keywords = ["old"]
authors = [{ name = "Old Author", email = "old@example.com" }]

[tool.poetry]
name = "test-pkg"
version = "1.0.0"
description = "Old"
license = "Apache-2.0"
authors = ["Old Author <old@example.com>"]
keywords = ["old"]
homepage = "https://example.com/old"
repository = "https://example.com/old-repo"

[tool.poetry.urls]
documentation = "https://example.com/old-docs"

[tool.poetry.dependencies]
python = "^3.10"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""


def test_poetry2_updates_existing_legacy_metadata(tmp_path, metadata):
    doc = sync(write(tmp_path, POETRY2), metadata)

    assert doc["project"]["version"] == "2.0.0"
    legacy = doc["tool"]["poetry"]
    assert legacy["version"] == "2.0.0"
    assert legacy["description"] == "New description"
    assert legacy["license"] == "MIT"
    assert list(legacy["keywords"]) == ["new", "words"]
    assert list(legacy["authors"]) == ["Jane Roe <jane@example.com>"]
    assert legacy["homepage"] == "https://example.com/new"
    assert legacy["repository"] == "https://example.com/new-repo"
    assert legacy["urls"]["documentation"] == "https://example.com/new-docs"
    assert legacy["dependencies"]["python"] == "^3.10"


def test_poetry2_legacy_license_updated_with_text_table_in_project(
    tmp_path, metadata, caplog
):
    text = POETRY2.replace(
        'license = "Apache-2.0"\nkeywords = ["old"]',
        'license = { text = "Apache-2.0" }\nkeywords = ["old"]',
        1,
    )
    with caplog.at_level(logging.WARNING, logger="somesy"):
        doc = sync(write(tmp_path, text), metadata)
    assert doc["project"]["license"] == "MIT"
    assert doc["tool"]["poetry"]["license"] == "MIT"
    assert "kept" not in caplog.text


def test_poetry2_never_adds_keys_to_legacy_table(tmp_path, metadata):
    text = (
        POETRY2.split("[tool.poetry]")[0]
        + '[tool.poetry.dependencies]\npython = "^3.10"\n\n[build-system]\n'
        + POETRY2.split("[build-system]\n")[1]
    )
    doc = sync(write(tmp_path, text), metadata)
    assert dict(doc["tool"]["poetry"]) == {"dependencies": {"python": "^3.10"}}


def test_poetry2_legacy_metadata_respects_dynamic(tmp_path, metadata):
    text = POETRY2.replace(
        'name = "test-pkg"\nversion = "1.0.0"\ndescription = "Old"\nlicense = "Apache-2.0"\nkeywords',
        'name = "test-pkg"\ndescription = "Old"\nlicense = "Apache-2.0"\nkeywords',
        1,
    ).replace("[tool.poetry]\nname", 'dynamic = ["version"]\n\n[tool.poetry]\nname', 1)
    doc = sync(write(tmp_path, text), metadata)
    assert doc["tool"]["poetry"]["version"] == "1.0.0"
    assert "version" not in doc["project"]


# ---- B5 ----


def test_poetry_sync_does_not_leave_instance_attribute(tmp_path, metadata):
    path = write(tmp_path, POETRY2)
    writer = Poetry(path, version=2)
    writer.sync(metadata)
    assert "_from_person" not in vars(writer)
    # v2 persons are still written as tables
    assert writer._data["project"]["authors"][0]["name"] == "Jane Roe"


# ---- B6 url spelling ----


def urls_doc(urls):
    return HEAD + 'version = "1.0.0"\ndescription = "Old"\n\n[project.urls]\n' + urls


def test_duplicate_url_spellings_update_first_and_warn(tmp_path, metadata, caplog):
    path = write(
        tmp_path,
        urls_doc('homepage = "https://a.example"\nHomepage = "https://b.example"\n'),
    )
    with caplog.at_level(logging.WARNING, logger="somesy"):
        doc = sync(path, metadata)
    urls = doc["project"]["urls"]
    assert urls["homepage"] == "https://example.com/new"
    assert urls["Homepage"] == "https://b.example"
    assert "Homepage" in caplog.text


def test_new_url_keys_follow_predominant_spelling(tmp_path, metadata):
    path = write(
        tmp_path,
        urls_doc(
            'Homepage = "https://a.example"\nChangelog = "https://c.example"\n'
            'issues = "https://d.example"\n'
        ),
    )
    urls = sync(path, metadata)["project"]["urls"]
    assert urls["Homepage"] == "https://example.com/new"
    assert urls["Repository"] == "https://example.com/new-repo"
    assert "repository" not in urls


def test_mixed_case_existing_key_is_updated_in_place(tmp_path, metadata):
    path = write(
        tmp_path,
        urls_doc('Homepage = "https://a.example"\nrepository = "https://r.example"\n'),
    )
    urls = sync(path, metadata)["project"]["urls"]
    assert urls["Homepage"] == "https://example.com/new"
    assert urls["repository"] == "https://example.com/new-repo"
    assert set(urls) == {"Homepage", "repository", "documentation"} or set(urls) == {
        "Homepage",
        "repository",
        "Documentation",
    }
