import pytest

from somesy.commands.init_config import init_config


@pytest.fixture
def cli_options() -> dict:
    return {
        "no_sync_cff": False,
        "cff_file": "CITATION.cff",
        "no_sync_pyproject": False,
        "pyproject_file": "pyproject.toml",
        "show_info": False,
        "verbose": False,
        "debug": False,
    }


def test_init_config(
    tmp_path,
    create_somesy_metadata,
    create_somesy_metadata_config,
    create_poetry_file,
    cli_options,
):
    # load empty file
    # reject_file = tmp_path / ".somesy.reject.toml"
    # reject_file.touch()
    # options = dict(cli_options)
    # options["debug"] = True
    # with pytest.raises(ValueError):
    #     init_config(reject_file, options)

    # load somesy file
    somesy_file = tmp_path / ".somesy.toml"
    create_somesy_metadata(somesy_file)
    options = dict(cli_options)
    options["debug"] = True
    init_config(somesy_file, options)
    assert "debug = true" in somesy_file.read_text()

    # load somesy file with config
    somesy_file = tmp_path / ".somesy.with_config.toml"
    create_somesy_metadata_config(somesy_file)
    options = dict(cli_options)
    options["show_info"] = True
    init_config(somesy_file, options)
    assert "show_info = true" in somesy_file.read_text()

    # load pyproject file
    pyproject_file = tmp_path / "pyproject.toml"
    create_poetry_file(pyproject_file)
    options = dict(cli_options)
    options["debug"] = True
    init_config(pyproject_file, options)
    assert "debug = true" in pyproject_file.read_text()
