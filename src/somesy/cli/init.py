"""Set config files for somesy."""
import logging
import traceback
from pathlib import Path

import typer

from somesy.cli.models import SyncCommandOptions
from somesy.commands import init_config
from somesy.core.discover import discover_input
from somesy.core.utils import set_logger

logger = logging.getLogger("somesy")
app = typer.Typer()


@app.command()
def config():
    """Set CLI configs for somesy."""
    set_logger(debug=False, verbose=False, info=False)
    try:
        # check if input file exists, if not, try to find it from default list
        input_file_default = discover_input()

        options = SyncCommandOptions()

        # prompt for inputs
        input_file = typer.prompt("Input file path", default=input_file_default)
        input_file = Path(input_file)
        options.input_file = input_file
        options.no_sync_cff = not typer.confirm(
            "Do you want to sync CFF file?", default=True
        )

        cff_file = typer.prompt("CFF file path", default="CITATION.cff")
        if cff_file is not None or cff_file != "":
            options.cff_file = cff_file

        options.no_sync_pyproject = not typer.confirm(
            "Do you want to sync pyproject.toml file?", default=True
        )

        pyproject_file = typer.prompt(
            "pyproject.toml file path", default="pyproject.toml"
        )
        if pyproject_file is not None or pyproject_file != "":
            options.pyproject_file = pyproject_file

        options.show_info = typer.confirm(
            "Do you want to show info about the sync process?"
        )
        options.verbose = typer.confirm("Do you want to show verbose logs?")
        options.debug = typer.confirm("Do you want to show debug logs?")
        set_logger(debug=options.debug, verbose=options.verbose, info=options.show_info)

        logger.debug(f"CLI options entered: {options}")

        init_config(input_file, options)
        logger.info(
            f"[bold green]Input file is updated/created at {input_file}[/bold green]"
        )

    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)
