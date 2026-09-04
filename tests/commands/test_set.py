"""Tests for the project metadata set command."""

import pytest
from typer.testing import CliRunner

from somesy.commands import set_project_value
from somesy.core.core import get_input_content
from somesy.main import app

runner = CliRunner()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "renamed-project"),
        ("description", "A revised description."),
        ("version", "1.2.3"),
        ("license", "MIT"),
        ("homepage", "https://example.com"),
        ("repository", "https://github.com/example/project"),
        ("documentation", "https://docs.example.com"),
    ],
)
def test_set_project_value(tmp_path, create_files, file_types, field, value):
    """Update each supported scalar project value."""
    create_files({(file_types.SOMESY, "somesy.toml")})
    input_file = tmp_path / "somesy.toml"

    set_project_value(input_file, field, value)

    project = get_input_content(input_file)["project"]
    assert project[field] == value
    if field != "description":
        assert (
            project["description"]
            == "This is a test project for demonstration purposes."
        )


def test_set_command_updates_project_value(
    tmp_path, create_files, file_types, monkeypatch
):
    """Wire the command arguments to the project metadata update."""
    create_files({(file_types.SOMESY, "somesy.toml")})
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["set", "name", "renamed-project"])

    assert result.exit_code == 0, result.stdout
    assert (
        get_input_content(tmp_path / "somesy.toml")["project"]["name"]
        == "renamed-project"
    )


@pytest.mark.parametrize(
    ("arguments", "error"),
    [
        (["set", "keywords", "metadata"], "Unknown project field 'keywords'"),
        (
            ["set", "name", "renamed-project", "--input-file", "pyproject.toml"],
            "The input file must be a somesy.toml file.",
        ),
    ],
)
def test_set_command_rejects_unsupported_input(
    tmp_path, create_files, file_types, monkeypatch, arguments, error
):
    """Report invalid fields and input files through the Typer command."""
    create_files(
        {
            (file_types.SOMESY, "somesy.toml"),
            (file_types.POETRY, "pyproject.toml"),
        }
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, arguments)

    assert result.exit_code == 1
    assert error in result.stdout
