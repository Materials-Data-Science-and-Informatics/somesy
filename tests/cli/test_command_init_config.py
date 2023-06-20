from pathlib import Path

from typer.testing import CliRunner

from somesy.main import app

runner = CliRunner()


def test_cli_config_init(tmp_path, create_poetry_file):
    input_file = tmp_path / ".somesy.toml"
    input_file.write_text(Path("tests/core/data/.somesy.with_config.toml").read_text())
    cff_file = tmp_path / "CITATION.cff"
    pyproject_file = tmp_path / "pyproject.toml"
    codemeta_file = tmp_path / "codemeta.json"
    create_poetry_file(pyproject_file)

    command_inputs = []

    # Input file path
    command_inputs.append(f"{input_file}\n")

    # no_sync_cff
    command_inputs.append("y\n")

    # CFF file path
    command_inputs.append(f"{cff_file}\n")

    # no_sync_pyproject
    command_inputs.append("y\n")

    # pyproject.toml file path
    command_inputs.append(f"{pyproject_file}\n")

    # no_sync_codemeta
    command_inputs.append("y\n")

    # codemeta.json file path
    command_inputs.append(f"{codemeta_file}\n")

    # show_info
    command_inputs.append("\n")

    # verbose
    command_inputs.append("\n")

    # debug
    command_inputs.append("y\n")

    command_input = "".join(command_inputs)

    # test with correct inputs
    result = runner.invoke(
        app,
        [
            "init",
            "config",
        ],
        input=command_input,
    )
    assert result.exit_code == 0
    assert "Input file is updated/created at" in result.stdout
    assert f'cff_file = "{cff_file}"' in input_file.read_text()
    assert f'pyproject_file = "{pyproject_file}"' in input_file.read_text()
    assert "no_sync_cff = false" in input_file.read_text()

    # test with incorrect inputs
    pyproject_file.unlink()
    result = runner.invoke(
        app,
        [
            "init",
            "config",
        ],
        input=f"{pyproject_file}\n\n{cff_file}\n\n{pyproject_file}\n\ny\n",
    )
    assert result.exit_code == 1
    assert "No such file or directory" in result.stdout
