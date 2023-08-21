from pathlib import Path

from typer.testing import CliRunner

from somesy.core import core
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
            "-vvv",
            "sync",
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
    print(result.output)
    assert result.exit_code == 0
    assert "Metadata synchronization completed." in result.stdout
    assert not cff_file.is_file()  # disabled in input_file!
    assert pyproject_file.is_file()
    assert codemeta_file.is_file()

    # create an error in the input file
    mocker.patch.object(core, "INPUT_FILES_ORDERED", [])
    input_file_reject = Path("tests/core/data/.somesy2.toml")
    result = runner.invoke(
        app,
        [
            "-vvv",
            "sync",
            "-i",
            str(input_file_reject),
        ],
    )
    assert result.exit_code == 1
    assert "No somesy input file found." in result.stdout
