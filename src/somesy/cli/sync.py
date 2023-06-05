"""Main entry point for the somesy CLI."""
import logging
import traceback
from pathlib import Path

import typer

from somesy.cli.models import SyncCommandOptions
from somesy.cli.utils import get_cli_file_input
from somesy.cli.validators import get_prioritized_sync_command_inputs
from somesy.commands import sync as sync_command
from somesy.core.discover import discover_input
from somesy.core.utils import set_logger

logger = logging.getLogger("somesy")
app = typer.Typer()


@app.callback(invoke_without_command=True)
def sync(
    input_file: Path = typer.Option(
        None,
        "--input-file",
        "-i",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Somesy input file path (default: .somesy.toml)",
    ),
    no_sync_cff: bool = typer.Option(
        None,
        "--no-sync-cff",
        "-C",
        help="Do not sync CITATION.cff file (default: False)",
    ),
    cff_file: Path = typer.Option(
        None,
        "--cff-file",
        "-c",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="CITATION.cff file path (default: CITATION.cff)",
    ),
    no_sync_pyproject: bool = typer.Option(
        None,
        "--no-sync-pyproject",
        "-P",
        help="Do not sync pyproject.toml file (default: False)",
    ),
    pyproject_file: Path = typer.Option(
        None,
        "--pyproject-file",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Existing pyproject.toml file path (default: pyproject.toml)",
    ),
    show_info: bool = typer.Option(
        None,
        "--show-info",
        "-s",
        help="Get basic output (somesy is quiet by default) (default: False)",
    ),
    verbose: bool = typer.Option(
        None,
        "--verbose",
        "-v",
        help="Verbose output (default: False)",
    ),
    debug: bool = typer.Option(
        None,
        "--debug",
        "-d",
        help="Debug output (default: False)",
    ),
):
    """Sync project metadata input with metadata files."""
    set_logger(debug=debug, verbose=verbose, info=show_info)

    try:
        # check if input file exists, if not, try to find it from default list
        input_file = discover_input(input_file)

        # get prioritized inputs
        cli_inputs = SyncCommandOptions(
            no_sync_cff=no_sync_cff,
            cff_file=cff_file,
            no_sync_pyproject=no_sync_pyproject,
            pyproject_file=pyproject_file,
            show_info=show_info,
            verbose=verbose,
            debug=debug,
        )
        logger.debug(
            f"CLI arguments:\n{input_file=}, {no_sync_cff=}, {cff_file=}, {no_sync_pyproject=}, {pyproject_file=}, {verbose=}, {debug=}"
        )

        file_cli_input = get_cli_file_input(input_file)
        logger.debug(f"File CLI arguments:\n{file_cli_input}")

        validated_inputs = get_prioritized_sync_command_inputs(
            cli_options=cli_inputs, file_options=file_cli_input
        )

        logger.info("[bold green]Syncing project metadata...[/bold green]\n")

        # info output
        logger.info("Files to sync:")
        if not validated_inputs["no_sync_pyproject"]:
            logger.info(
                f"  - [italic]Pyproject.toml[/italic] [grey]({pyproject_file})[/grey]"
            )

        if not validated_inputs["no_sync_cff"]:
            logger.info(f"  - [italic]CITATION.cff[/italic] [grey]({cff_file})[/grey]")

        # sync files
        sync_command(
            input_file=input_file,
            pyproject_file=validated_inputs["pyproject_file"]
            if not validated_inputs["no_sync_pyproject"]
            else None,
            cff_file=validated_inputs["cff_file"]
            if not validated_inputs["no_sync_cff"]
            else None,
        )

        logger.info("[bold green]Syncing completed.[/bold green]")
    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)
