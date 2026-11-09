import json
from datetime import datetime, timezone

import pytest

from somesy.codemeta import CodeMeta
from somesy.core.core import write_json


def test_update_codemeta(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"

    cm = CodeMeta(codemeta_file, merge=False)

    # firstly, create a codemeta file
    cm.sync(somesy_input.project)
    cm.save()

    assert codemeta_file.is_file()
    assert json.loads(codemeta_file.read_text())["identifier"] == (
        "https://doi.org/10.5281/zenodo.1234567"
    )
    dat = open(codemeta_file, "rb").read()
    assert dat.endswith(b"}\n")
    assert not dat.endswith(b"}\n\n")

    # second time, no changes but codemeta.json exists -> codemeta.json is the same
    cm.sync(somesy_input.project)
    cm.save()
    assert codemeta_file.is_file()
    dat2 = open(codemeta_file, "rb").read()
    assert dat == dat2

    # third time, change the project name -> codemeta.json is different
    somesy_input.project.name = "new_name"
    cm.sync(somesy_input.project)
    cm.save()
    assert codemeta_file.is_file()
    dat3 = open(codemeta_file, "rb").read()
    assert dat != dat3

    # fourth time, change the project name back and change version in codemeta.json
    # -> codemeta.json is the same
    somesy_input.project.name = "testproject"
    codemeta = json.loads(dat3)
    codemeta["version"] = "0.0.2"
    write_json(codemeta, codemeta_file)
    cm.sync(somesy_input.project)
    cm.save()
    assert codemeta_file.is_file()
    dat4 = open(codemeta_file, "rb").read()
    assert dat == dat4
    assert dat3 != dat4


def test_multiple_licenses(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    somesy_input.project.license = [
        somesy_input.project.license,
        "Apache-2.0",
    ]
    cm = CodeMeta(codemeta_file, merge=False)
    cm.sync(somesy_input.project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["license"] == [
        "https://spdx.org/licenses/MIT",
        "https://spdx.org/licenses/Apache-2.0",
    ]


def test_codemeta_writes_contribution_roles(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"

    cm = CodeMeta(codemeta_file)
    cm.sync(somesy_input.project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["@context"] == "https://w3id.org/codemeta/3.1"

    author_person = next(
        person
        for person in data["author"]
        if person.get("givenName") == "John" and person.get("@type") == "Person"
    )
    author_roles = [
        role
        for role in data["author"]
        if role.get("@type") == "Role" and role["schema:author"] == author_person["@id"]
    ]
    assert {role["roleName"] for role in author_roles} == {
        "The main developer, maintainer, and tester.",
        "maintenance",
        "code",
        "test",
        "review",
        "doc",
    }
    assert {role["startDate"] for role in author_roles} == {"2023-01-15"}

    contributor_person = next(
        person
        for person in data["contributor"]
        if person.get("givenName") == "Michael" and person.get("@type") == "Person"
    )
    contributor_role = next(
        role
        for role in data["contributor"]
        if role.get("@type") == "Role"
        and role["schema:author"] == contributor_person["@id"]
    )
    assert (
        contributor_role["roleName"]
        == "Valuable input concerning metadata standards and usability."
    )
    assert contributor_role["startDate"] == "2023-03-10"


def test_update_codemeta_with_merge(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"

    # Create initial codemeta file with some data and extra fields
    initial_data = {
        "@context": [
            "https://doi.org/10.5063/schema/codemeta-2.0",
            "https://schema.org",
        ],
        "@type": "SoftwareSourceCode",
        "name": "original_name",
        "version": "0.0.1",
        "author": [{"@type": "Person", "name": "Original Author"}],
        "downloadUrl": "https://example.com/download",
        "funder": {"@type": "Organization", "name": "Original Funder"},
        "contIntegration": "https://example.com/ci",
        "embargoDate": "2024-01-01",
    }
    write_json(initial_data, codemeta_file)

    # Initialize CodeMeta with merge=True
    cm = CodeMeta(codemeta_file, merge=True)
    cm.sync(somesy_input.project)
    cm.save()

    # Check if file exists and verify merged content
    assert codemeta_file.is_file()
    with open(codemeta_file, "r") as f:
        data = json.load(f)
        assert data["version"] == "1.0.0"
        assert data["@context"] == [
            "https://w3id.org/codemeta/3.1",
            "https://schema.org",
        ]
        # Check if original fields are preserved
        assert data["downloadUrl"] == "https://example.com/download"
        assert data["funder"]["@type"] == "Organization"
        assert data["funder"]["name"] == "Original Funder"
        assert data["continuousIntegration"] == "https://example.com/ci"
        assert data["embargoEndDate"] == "2024-01-01"
        assert "contIntegration" not in data
        assert "embargoDate" not in data
        # Check if additional contexts are preserved
        assert "https://doi.org/10.5063/schema/codemeta-2.0" not in data["@context"]
        assert "https://schema.org" in data["@context"]
        # Verify type is preserved
        assert data["@type"] == "SoftwareSourceCode"
        # Verify authors are overwritten (not merged)
        assert data["author"] != initial_data["author"]


def test_update_codemeta_preserves_inline_context(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    inline_context = {"example": "https://example.com/"}
    codemeta_file.write_text(
        json.dumps(
            {
                "@context": [
                    "https://doi.org/10.5063/schema/codemeta-2.0",
                    inline_context,
                ],
                "@type": "SoftwareSourceCode",
                "name": "original_name",
            }
        )
    )

    cm = CodeMeta(codemeta_file, merge=True)
    cm.sync(somesy_input.project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["@context"] == ["https://w3id.org/codemeta/3.1", inline_context]


def test_update_codemeta_migrates_codemetapy_v2_output(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    codemetapy_context = [
        "https://doi.org/10.5063/schema/codemeta-2.0",
        "https://w3id.org/software-iodata",
        "https://raw.githubusercontent.com/jantman/repostatus.org/master/badges/latest/ontology.jsonld",
        "https://schema.org",
        "https://w3id.org/software-types",
    ]
    codemeta_file.write_text(
        json.dumps(
            {
                "@context": codemetapy_context,
                "@type": "SoftwareSourceCode",
                "name": "original_name",
                "developmentStatus": "https://www.repostatus.org/#active",
                "targetProduct": {
                    "@type": "WebApplication",
                    "url": "https://example.com",
                },
            }
        )
    )

    cm = CodeMeta(codemeta_file, merge=True)
    cm.sync(somesy_input.project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["@context"] == [
        "https://w3id.org/codemeta/3.1",
        *codemetapy_context[1:],
    ]
    assert data["developmentStatus"] == "https://www.repostatus.org/#active"
    assert data["targetProduct"] == {
        "@type": "WebApplication",
        "url": "https://example.com",
    }


def test_codemeta_roundtrip_non_orcid_contributor_with_role(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    project = somesy_input.project.model_copy(deep=True)
    michael = next(p for p in project.people if p.given_names == "Michael")
    michael.orcid = None  # no ORCID, but a contribution role is written

    cm = CodeMeta(codemeta_file)
    cm.sync(project)
    cm.save()

    harvested = CodeMeta(codemeta_file, merge=True).harvest_metadata()
    names = [p.given_names for p in harvested["people"] if hasattr(p, "given_names")]
    assert names.count("Michael") == 1


def test_codemeta_harvests_authors(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    cm = CodeMeta(codemeta_file)
    cm.sync(somesy_input.project)
    cm.save()

    harvested = CodeMeta(codemeta_file).harvest_metadata()
    assert any(p.given_names == "John" for p in harvested["people"])


def test_merge_removes_old_doi_keeps_other_identifiers(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    initial = {
        "@context": "https://w3id.org/codemeta/3.1",
        "@type": "SoftwareSourceCode",
        "name": "x",
        "identifier": ["https://doi.org/10.1/old", "other-id"],
    }
    codemeta_file.write_text(json.dumps(initial))
    project = somesy_input.project.model_copy(update={"doi": None})

    cm = CodeMeta(codemeta_file, merge=True)
    cm.sync(project)
    assert cm._data["identifier"] == "other-id"


def test_merge_warns_when_both_ci_keys_exist(somesy_input, tmp_path, caplog):
    codemeta_file = tmp_path / "codemeta.json"
    initial = {
        "@context": "https://w3id.org/codemeta/3.1",
        "@type": "SoftwareSourceCode",
        "name": "x",
        "contIntegration": "https://old.example/ci",
        "continuousIntegration": "https://new.example/ci",
    }
    codemeta_file.write_text(json.dumps(initial))

    CodeMeta(codemeta_file, merge=True).sync(somesy_input.project)
    assert "contIntegration" in caplog.text


def test_merge_refreshes_fields_produced_by_enrichment(somesy_input, tmp_path, mocker):
    from datetime import date

    from somesy.git.models import GitMetadata

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'x'\ndependencies = ['requests>=3']\n")
    codemeta_file = tmp_path / "codemeta.json"
    write_json(
        {
            "@context": "https://w3id.org/codemeta/3.1",
            "@type": "SoftwareSourceCode",
            "name": "x",
            "version": "0.0.1",
            "codeRepository": "https://example.org/old",
            "dateModified": "2000-01-01",
            "dateCreated": "1999-01-01",
            "softwareRequirements": ["old-dependency"],
            "downloadUrl": "https://example.com/download",
            "readme": "https://example.org/old-readme",
        },
        codemeta_file,
    )
    mocker.patch(
        "somesy.codemeta.enrich.harvest_git",
        return_value=GitMetadata(
            repository="https://example.org/new.git",
            date_created=date(1999, 1, 1),
            date_modified=date(2024, 5, 6),
            version="v9",
        ),
    )
    project = somesy_input.project
    project.version = None  # version then comes from enrichment
    project.repository = None

    cm = CodeMeta(
        codemeta_file,
        merge=True,
        pass_validation=True,
        enrich_sources={"pyproject": pyproject},
        enrich_root=tmp_path,
    )
    cm.sync(project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["version"] == "v9"
    assert data["codeRepository"] == "https://example.org/new"
    # content changed -> modified today
    assert data["dateModified"] == datetime.now(timezone.utc).date().isoformat()
    assert data["dateCreated"] == "1999-01-01"
    assert data["softwareRequirements"][0]["name"] == "requests"
    # not produced by somesy -> kept
    assert data["downloadUrl"] == "https://example.com/download"
    # produced only if found in project files: not found here -> kept
    assert data["readme"] == "https://example.org/old-readme"


def test_merge_keeps_enrichable_fields_if_nothing_produces_them(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"
    write_json(
        {
            "@context": "https://w3id.org/codemeta/3.1",
            "@type": "SoftwareSourceCode",
            "name": "x",
            "dateModified": "2000-01-01",
            "runtimePlatform": "Old 1",
        },
        codemeta_file,
    )
    cm = CodeMeta(codemeta_file, merge=True, pass_validation=True)
    cm.sync(somesy_input.project)
    cm.save()
    data = json.loads(codemeta_file.read_text())
    assert data["dateModified"] == "2000-01-01"
    assert data["runtimePlatform"] == "Old 1"


def test_merge_enrichment_is_complete_after_sync(somesy_input, tmp_path, mocker):
    """Enrichment and restoring unrefreshed values happen in sync(), not save()."""
    from datetime import date

    from somesy.git.models import GitMetadata

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'x'\ndependencies = ['requests>=3']\n")
    codemeta_file = tmp_path / "codemeta.json"
    write_json(
        {
            "@context": "https://w3id.org/codemeta/3.1",
            "@type": "SoftwareSourceCode",
            "name": "x",
            "dateModified": "2000-01-01",
            "readme": "https://example.org/old-readme",
            "downloadUrl": "https://example.com/download",
            "softwareRequirements": ["old-dependency"],
        },
        codemeta_file,
    )
    mocker.patch(
        "somesy.codemeta.enrich.harvest_git",
        return_value=GitMetadata(date_modified=date(2024, 5, 6)),
    )
    cm = CodeMeta(
        codemeta_file,
        merge=True,
        pass_validation=True,
        enrich_sources={"pyproject": pyproject},
        enrich_root=tmp_path,
    )
    cm.sync(somesy_input.project)

    # _data is final right after sync: refreshed, kept and original key order
    assert cm._data["dateModified"] == datetime.now(timezone.utc).date().isoformat()
    assert cm._data["softwareRequirements"][0]["name"] == "requests"
    assert cm._data["readme"] == "https://example.org/old-readme"
    keys = list(cm._data)
    assert keys.index("dateModified") < keys.index("readme") < keys.index("downloadUrl")
    assert not hasattr(cm, "_stale")
    assert not hasattr(cm, "_key_order")


def _git_codemeta(mocker, tmp_path, merge, version, modified, created=None):
    """Return a CodeMeta writer enriched from mocked Git metadata."""
    from somesy.git.models import GitMetadata

    mocker.patch(
        "somesy.codemeta.enrich.harvest_git",
        return_value=GitMetadata(
            version=version, date_modified=modified, date_created=created
        ),
    )
    return CodeMeta(
        tmp_path / "codemeta.json",
        merge=merge,
        pass_validation=True,
        enrich_sources={},
        enrich_root=tmp_path,
    )


@pytest.mark.parametrize("merge", [False, True])
def test_git_values_kept_if_nothing_else_changed(somesy_input, tmp_path, mocker, merge):
    """A new tag or commit alone does not change codemeta.json (issue #156)."""
    from datetime import date

    codemeta_file = tmp_path / "codemeta.json"
    project = somesy_input.project
    project.version = None  # version then comes from the Git tag

    cm = _git_codemeta(mocker, tmp_path, merge, "v1.0.0", date(2024, 1, 1))
    cm.sync(project)
    cm.save()
    data = json.loads(codemeta_file.read_text())
    data["dateModified"] = "2000-01-01"
    write_json(data, codemeta_file)
    first = codemeta_file.read_bytes()

    cm = _git_codemeta(mocker, tmp_path, merge, "v2.0.0", date(2024, 2, 2))
    cm.sync(project)
    cm.save()

    assert codemeta_file.read_bytes() == first


@pytest.mark.parametrize("merge", [False, True])
def test_git_values_refreshed_if_other_content_changed(
    somesy_input, tmp_path, mocker, merge
):
    from datetime import date

    codemeta_file = tmp_path / "codemeta.json"
    project = somesy_input.project
    project.version = None

    cm = _git_codemeta(mocker, tmp_path, merge, "v1.0.0", date(2024, 1, 1))
    cm.sync(project)
    cm.save()
    data = json.loads(codemeta_file.read_text())
    data["dateModified"] = "2000-01-01"
    write_json(data, codemeta_file)

    project.name = "renamed"
    cm = _git_codemeta(mocker, tmp_path, merge, "v2.0.0", date(2024, 2, 2))
    cm.sync(project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["version"] == "v2.0.0"
    assert data["dateModified"] == datetime.now(timezone.utc).date().isoformat()


@pytest.mark.parametrize("merge", [False, True])
def test_canonical_version_is_always_used(somesy_input, tmp_path, mocker, merge):
    from datetime import date

    codemeta_file = tmp_path / "codemeta.json"
    project = somesy_input.project
    project.version = "1.0.0"
    cm = _git_codemeta(mocker, tmp_path, merge, "v9", date(2024, 1, 1))
    cm.sync(project)
    cm.save()

    project.version = "2.0.0"
    cm = _git_codemeta(mocker, tmp_path, merge, "v9", date(2024, 1, 1))
    cm.sync(project)
    cm.save()

    data = json.loads(codemeta_file.read_text())
    assert data["version"] == "2.0.0"
    assert data["dateModified"] == datetime.now(timezone.utc).date().isoformat()


@pytest.mark.parametrize("merge", [False, True])
def test_unknown_creation_date_keeps_previous(somesy_input, tmp_path, mocker, merge):
    """A shallow clone (no creation date from Git) does not drop dateCreated."""
    from datetime import date

    codemeta_file = tmp_path / "codemeta.json"
    project = somesy_input.project
    cm = _git_codemeta(mocker, tmp_path, merge, None, None, date(2020, 1, 1))
    cm.sync(project)
    cm.save()
    first = codemeta_file.read_bytes()
    assert json.loads(first)["dateCreated"] == "2020-01-01"

    cm = _git_codemeta(mocker, tmp_path, merge, None, None, created=None)
    cm.sync(project)
    cm.save()

    assert codemeta_file.read_bytes() == first
