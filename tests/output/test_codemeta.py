from somesy.codemeta import CodeMeta
from somesy.json_wrapper import json


def test_update_codemeta(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"

    cm = CodeMeta(codemeta_file, merge=False)

    # firstly, create a codemeta file
    cm.sync(somesy_input.project)
    cm.save()

    assert codemeta_file.is_file()
    dat = open(codemeta_file, "rb").read()

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
        assert "https://w3id.org/software-types" in data["@context"]
        # Check if original fields are preserved
        assert data["downloadUrl"] == "https://example.com/download"
        assert data["funder"]["@type"] == "Organization"
        assert data["funder"]["name"] == "Original Funder"
        # Check if additional contexts are preserved
        assert "https://doi.org/10.5063/schema/codemeta-2.0" in data["@context"]
        assert "https://schema.org" in data["@context"]
        # Verify type is preserved
        assert data["@type"] == "SoftwareSourceCode"
        # Verify authors are overwritten (not merged)
        assert data["author"] != initial_data["author"]
