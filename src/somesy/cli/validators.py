"""Functions to validate and prioritize CLI inputs."""
import logging
from pathlib import Path

import typer

from somesy.cli.models import SyncCommandOptions

logger = logging.getLogger("somesy")

SYNC_COMMAND_DEFAULTS = {
    "input_file": Path(".somesy.toml"),
    "no_sync_cff": False,
    "cff_file": Path("CITATION.cff"),
    "no_sync_pyproject": False,
    "pyproject_file": Path("pyproject.toml"),
    "show_info": False,
    "verbose": False,
    "debug": False,
}


def get_prioritized_sync_command_inputs(
    cli_options: SyncCommandOptions, file_options: SyncCommandOptions
) -> dict:
    """Prioritize sync command inputs and return prioritized inputs.

    Check direct cli inputs which has the highest priority, then check file inputs and both of them does not have the config, use defaults.

    Args:
        cli_options (dict): _description_
        file_options (_type_): _description_

    Returns:
        dict: _description_
    """
    validated_inputs = {}

    for key, value in SYNC_COMMAND_DEFAULTS.items():
        if getattr(cli_options, key) is not None:
            validated_inputs[key] = getattr(cli_options, key)
        elif getattr(file_options, key) is not None:
            validated_inputs[key] = getattr(file_options, key)
        else:
            validated_inputs[key] = value

    # if a output file is given by cli input, use it
    if cli_options.cff_file is not None:
        validated_inputs["no_sync_cff"] = False
    if cli_options.pyproject_file is not None:
        validated_inputs["no_sync_pyproject"] = False

    # at least one of the sync options must be enabled
    if validated_inputs["no_sync_cff"] and validated_inputs["no_sync_pyproject"]:
        logger.warning("There should be at least one file to sync.")
        typer.Exit(code=0)

    logger.debug(f"validated inputs: {validated_inputs}")
    return validated_inputs
