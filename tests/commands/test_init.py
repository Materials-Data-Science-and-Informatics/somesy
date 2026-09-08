"""Tests for the metadata initialization command."""

import json
import subprocess
import warnings

import pytest
from typer.testing import CliRunner

from somesy.core.core import get_input_content
from somesy.core.models import SomesyInput
from somesy.git.models import GitAuthor, GitMetadata
from somesy.main import app

runner = CliRunner()


def test_init_harvests_project_file_and_git_authors(
    tmp_path, create_files, file_types, monkeypatch
):
    """Create Somesy metadata from a project file and Git history."""
    create_files({(file_types.POETRY, "pyproject.toml")})
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Git Author"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "git@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0, result.stdout
    content = get_input_content(tmp_path / "somesy.toml")
    assert content["project"]["name"] == "test-package"
    assert "entities" not in content["project"]
    assert any(
        person["email"] == "git@example.com" for person in content["project"]["people"]
    )
    assert "no_sync_cff" not in content["config"]
    assert "no_sync_codemeta" not in content["config"]
    assert "no_sync_pyproject" not in content["config"]
    assert content["config"]["no_sync_package_json"] is True


def test_init_prompts_for_missing_required_metadata(tmp_path, monkeypatch):
    """Prompt only for required fields absent from harvested metadata."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("somesy.cli.init.harvest_sources", lambda _: [])
    monkeypatch.setattr("somesy.cli.init.harvest_git", lambda _: None)

    result = runner.invoke(
        app,
        ["init"],
        input="example\nA project\nMIT\nperson\nJane\nDoe\n\n",
    )

    assert result.exit_code == 0, result.stdout
    content = get_input_content(tmp_path / "somesy.toml")
    assert content["project"]["name"] == "example"
    assert content["project"]["license"] == "MIT"
    assert content["project"]["people"][0]["given-names"] == "Jane"


def test_init_prompts_for_entity_author_and_partial_metadata(tmp_path, monkeypatch):
    """Prompt only for missing fields and support an organization author."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "somesy.cli.init.harvest_sources",
        lambda _: [(tmp_path / "pyproject.toml", {"name": "harvested"})],
    )
    monkeypatch.setattr("somesy.cli.init.harvest_git", lambda _: None)

    result = runner.invoke(
        app,
        ["init"],
        input="A project\nMIT\nentity\nExample Org\norg@example.com\n",
    )

    assert result.exit_code == 0, result.stdout
    content = get_input_content(tmp_path / "somesy.toml")
    assert content["project"]["name"] == "harvested"
    assert content["project"]["description"] == "A project"
    assert content["project"]["entities"][0]["name"] == "Example Org"
    assert content["project"]["entities"][0]["email"] == "org@example.com"


def test_init_non_interactive_writes_partial_metadata(tmp_path, monkeypatch, caplog):
    """Write harvested metadata without prompting and warn about missing fields."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "somesy.cli.init.harvest_sources",
        lambda _: [(tmp_path / "pyproject.toml", {"name": "harvested"})],
    )
    monkeypatch.setattr("somesy.cli.init.harvest_git", lambda _: None)
    monkeypatch.setattr(
        "somesy.cli.init.typer.prompt",
        lambda *_, **__: (_ for _ in ()).throw(AssertionError("unexpected prompt")),
    )

    result = runner.invoke(app, ["init", "--non-interactive"])

    assert result.exit_code == 0, result.stdout
    content = get_input_content(tmp_path / "somesy.toml")
    assert content["project"] == {"name": "harvested"}
    assert "pass_validation" not in content["config"]
    assert [
        record.message for record in caplog.records if record.levelname == "WARNING"
    ] == [
        "Missing required metadata: description",
        "Missing required metadata: license",
        "Missing required metadata: author",
    ]


def test_init_non_interactive_recognizes_git_author(tmp_path, monkeypatch, caplog):
    """Do not warn when Git supplies the required author."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "somesy.cli.init.harvest_sources",
        lambda _: [
            (
                tmp_path / "pyproject.toml",
                {"name": "project", "description": "description", "license": "MIT"},
            )
        ],
    )
    monkeypatch.setattr(
        "somesy.cli.init.harvest_git",
        lambda _: GitMetadata(authors=[GitAuthor(name="Jane Doe")]),
    )

    result = runner.invoke(app, ["init", "--non-interactive"])

    assert result.exit_code == 0, result.stdout
    assert not [record for record in caplog.records if record.levelname == "WARNING"]
    content = get_input_content(tmp_path / "somesy.toml")
    assert content["project"]["people"][0]["author"] is True


def test_non_interactive_partial_init_can_sync_codemeta(tmp_path, monkeypatch, caplog):
    """Normalize harvested values and sync dependencies without a description."""
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps(
            {
                "name": "pipeline-project",
                "version": "1.2.3",
                "license": "MIT",
                "dependencies": {"chalk": "^5.4.1", "lodash": "^4.17.21"},
                "engines": {"node": ">=20"},
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "somesy.cli.init.harvest_git",
        lambda _: GitMetadata(authors=[GitAuthor(name="Jane Doe")]),
    )

    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="Pydantic serializer warnings.*")
        initialized = runner.invoke(app, ["init", "--non-interactive"])
        strict_sync = runner.invoke(app, ["sync"])
        synced = runner.invoke(app, ["sync", "--pass-validation"])

    assert initialized.exit_code == 0, initialized.stdout
    assert strict_sync.exit_code == 1
    assert synced.exit_code == 0, synced.stdout
    assert [record.message for record in caplog.records].count(
        "Missing required metadata: description"
    ) == 1
    codemeta = json.loads((tmp_path / "codemeta.json").read_text())
    assert "description" not in codemeta
    assert "abstract" not in codemeta
    assert {dependency["name"] for dependency in codemeta["softwareRequirements"]} == {
        "chalk",
        "lodash",
    }


def test_non_interactive_init_without_author_can_sync(tmp_path, monkeypatch):
    """Load and sync partial metadata without reapplying the author invariant."""
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "pipeline-project", "license": "MIT"})
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("somesy.cli.init.harvest_git", lambda _: None)

    initialized = runner.invoke(app, ["init", "--non-interactive"])
    synced = runner.invoke(app, ["sync", "--pass-validation"])

    assert initialized.exit_code == 0, initialized.stdout
    assert synced.exit_code == 0, synced.stdout
    codemeta = json.loads((tmp_path / "codemeta.json").read_text())
    assert codemeta["author"] == []


def test_partial_input_still_rejects_unknown_top_level_sections(tmp_path):
    path = tmp_path / "somesy.toml"
    path.write_text(
        "[project]\nname = 'project'\n\n[config]\npass_validation = true\n"
        "\n[unexpected]\nvalue = true\n"
    )

    with pytest.raises(ValueError):
        SomesyInput.from_input_file(path)
