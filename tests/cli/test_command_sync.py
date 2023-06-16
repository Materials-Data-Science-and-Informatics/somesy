from pathlib import Path

from typer.testing import CliRunner

from somesy.core import discover
from somesy.main import app

runner = CliRunner()


def test_app_sync(tmp_path, create_poetry_file, mocker):
    input_file = Path("tests/core/data/.somesy.with_config.toml")
    cff_file = tmp_path / "CITATION.cff"
    pyproject_file = tmp_path / "pyproject.toml"
    codemeta_file = tmp_path / "codemeta.json"

    # test sync without output files
    result = runner.invoke(
        app,
        [
            "sync",
            "-i",
            str(input_file),
            "--no-sync-pyproject",
            "--no-sync-cff",
            "--no-sync-codemeta",
        ],
    )
    assert result.exit_code == 1
    assert "nothing to do" in result.stdout

    # create pyproject file beforehand
    create_poetry_file(pyproject_file)

    # test sync with output files
    result = runner.invoke(
        app,
        [
            "sync",
            "-d",
            "-i",
            str(input_file),
            "-c",
            cff_file,
            "-p",
            pyproject_file,
            "-m",
            codemeta_file,
        ],
    )
    assert result.exit_code == 0
    assert "Syncing completed." in result.stdout
    assert not cff_file.exists()  # disabled in input_file!
    assert pyproject_file.exists()
    assert codemeta_file.exists()

    # create an error in the input file
    mocker.patch.object(discover, "INPUT_FILES_ORDERED", [])
    input_file_reject = Path("tests/core/data/.somesy2.toml")
    result = runner.invoke(
        app,
        [
            "sync",
            "-i",
            str(input_file_reject),
            "-d",
        ],
    )
    assert result.exit_code == 1
    assert "No somesy input file found." in result.stdout
