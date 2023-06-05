from pathlib import Path

from somesy.cli.models import SyncCommandOptions
from somesy.cli.utils import get_cli_file_input


def test_get_cli_file_input():
    # without config
    input_file = Path("tests/core/data/.somesy.toml")
    result = get_cli_file_input(input_file)
    assert result == SyncCommandOptions()

    input_file = Path("tests/core/data/.somesy.with_config.toml")
    result = get_cli_file_input(input_file)
    assert result.debug == True
    assert result.no_sync_cff == True
