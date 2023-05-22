from pathlib import Path

from typer.testing import CliRunner

from somesy.main import app

runner = CliRunner()


def test_app_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "somesy version: " in result.stdout

    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "somesy version: " in result.stdout


def test_app_sync(tmp_path):
    input_file = Path("tests/core/data/.somesy.toml").resolve()
    cff_file = tmp_path / "CITATION.cff"
    pyproject_file = tmp_path / "pyproject.toml"

    # test sync without output files
    result = runner.invoke(
        app,
        [
            "sync",
            "-i",
            str(input_file),
            "--no-sync-pyproject",
            "--no-sync-cff",
        ],
    )
    assert result.exit_code == 1

    # test sync with output files
    pyproject_file.touch()
    result = runner.invoke(
        app,
        [
            "sync",
            "-i",
            str(input_file),
            "-c",
            str(cff_file),
            "-p",
            str(pyproject_file),
            "-d",
        ],
    )
    assert result.exit_code == 0
    assert "Syncing completed." in result.stdout
    assert cff_file.exists()
    assert pyproject_file.exists()
