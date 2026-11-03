"""Set project metadata in a somesy.toml file."""

from pathlib import Path

import typer

from somesy.cli.util import existing_file_arg_config, wrap_exceptions
from somesy.commands import set_project_value
from somesy.core.core import discover_input


@wrap_exceptions
def set_value(
    field: str = typer.Argument(help="Project field to update."),
    value: str = typer.Argument(help="New field value."),
    input_file: Path | None = typer.Option(
        None,
        "--input-file",
        "-i",
        help="somesy input file (default: discovered .somesy.toml or somesy.toml).",
        **existing_file_arg_config,
    ),
):
    """Set a scalar project-metadata value in somesy.toml."""
    set_project_value(discover_input(input_file), field, value)
