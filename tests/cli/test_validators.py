from pathlib import Path

from somesy.cli.models import SyncCommandOptions
from somesy.cli.validators import get_prioritized_sync_command_inputs


def test_get_prioritized_sync_command_inputs():
    cli_options = {
        "input_file": Path("cli_input_file"),
        "no_sync_cff": True,
    }
    cli_options = SyncCommandOptions(**cli_options)
    file_options = {
        "cff_file": Path("file_cff_file"),
        "debug": True,
    }
    file_options = SyncCommandOptions(**file_options)

    expected = {
        "input_file": Path("cli_input_file"),
        "no_sync_cff": True,
        "cff_file": Path("file_cff_file"),
        "no_sync_pyproject": False,
        "pyproject_file": Path("pyproject.toml"),
        "show_info": False,
        "verbose": False,
        "debug": True,
    }
    assert get_prioritized_sync_command_inputs(cli_options, file_options) == expected
