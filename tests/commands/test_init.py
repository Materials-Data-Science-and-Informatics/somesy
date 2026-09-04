"""Tests for the metadata initialization command."""

import subprocess

from typer.testing import CliRunner

from somesy.core.core import get_input_content
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
    assert any(
        person["email"] == "git@example.com" for person in content["project"]["people"]
    )


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
