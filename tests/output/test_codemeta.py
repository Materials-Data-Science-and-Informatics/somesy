from somesy.codemeta import CodeMeta
from somesy.json_wrapper import json


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
    with open(codemeta_file, "w") as f:
        codemeta = json.loads(dat3)
        codemeta["version"] = "0.0.2"
        json.dump(codemeta, f)
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
    with open(codemeta_file, "w") as f:
        json.dump(initial_data, f)

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
