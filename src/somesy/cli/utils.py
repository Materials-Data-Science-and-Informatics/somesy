"""Utility functions for the CLI."""
from pathlib import Path

from somesy.cli.models import SyncCommandOptions
from somesy.core.core import get_somesy_cli_config


def get_cli_file_input(input_path: Path) -> SyncCommandOptions:
    """Mediate between CLI and file inputs.

    Args:
        input_path (Path): somesy config file path

    Returns:
        SyncCommandOptions: CLI inputs from the config file
    """
    file_inputs = get_somesy_cli_config(input_path)
    if file_inputs is None:
        return SyncCommandOptions()
    else:
        return SyncCommandOptions(**file_inputs.dict())
