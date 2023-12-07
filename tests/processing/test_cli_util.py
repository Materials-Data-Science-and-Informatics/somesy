from pathlib import Path

import pytest
from tomlkit import dump, load

from somesy.cli.util import resolved_somesy_input


@pytest.fixture
def somesy_file(create_files, file_types):
    folder_path = create_files([(file_types.SOMESY, "somesy.toml")])
    file_path = Path(folder_path) / "somesy.toml"
    somesy_file = None
    with open(file_path, "r") as f:
        somesy_file = load(f)

    # delete config section and add one property
    del somesy_file["config"]
    somesy_file["config"] = {"no_sync_package_json": False}

    # save to file
    with open(file_path, "w") as f:
        dump(somesy_file, f)
    return file_path


def test_resolved_somesy_input(somesy_file):
    # set cli_args for tests
    cli_args = {"input_file": somesy_file, "debug": True, "no_sync_pyproject": True}

    somesy_input = resolved_somesy_input(**cli_args)

    # check default values
    assert somesy_input.config.no_sync_cff is False
    assert somesy_input.config.pyproject_file == Path("pyproject.toml")

    # check overwritten values
    assert somesy_input.config.no_sync_pyproject is True

    # check newly add value
    assert somesy_input.config.debug is True
