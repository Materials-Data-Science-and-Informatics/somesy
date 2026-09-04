"""Set project metadata in a somesy.toml file."""

from pathlib import Path

import typer

from somesy.cli.util import existing_file_arg_config, wrap_exceptions
from somesy.commands import set_project_value


@wrap_exceptions
def set_value(
    field: str = typer.Argument(help="Project field to update."),
    value: str = typer.Argument(help="New field value."),
    input_file: Path = typer.Option(
        Path("somesy.toml"), "--input-file", "-i", **existing_file_arg_config
    ),
):
    """Set a scalar project-metadata value in somesy.toml."""
    set_project_value(input_file, field, value)
