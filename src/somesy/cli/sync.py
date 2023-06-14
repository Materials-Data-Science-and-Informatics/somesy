"""Sync command for somesy."""
import logging
import traceback
from pathlib import Path

import typer

from somesy.cli.utils import get_cli_file_input
from somesy.commands import sync as sync_command
from somesy.core.discover import discover_input
from somesy.core.models import SomesyCLIConfig
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
    no_sync_codemeta: bool = typer.Option(
        False,
        "--no-sync-codemeta",
        "-M",
        help="Do not sync codemeta.json file",
    ),
    codemeta_file: Path = typer.Option(
        Path("codemeta.json"),
        "--codemeta-file",
        "-m",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Custom codemeta.json file path",
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
        cli_inputs = SomesyCLIConfig(
            no_sync_cff=no_sync_cff,
            cff_file=cff_file,
            no_sync_pyproject=no_sync_pyproject,
            pyproject_file=pyproject_file,
            no_sync_codemeta=no_sync_codemeta,
            codemeta_file=codemeta_file,
            show_info=show_info,
            verbose=verbose,
            debug=debug,
        )
        cli_inputs = cli_inputs.dict(exclude_none=True, exclude_defaults=True)
        logger.debug(
            f"CLI arguments:\n{input_file=}, {no_sync_cff=}, {cff_file=}, {no_sync_pyproject=}, {pyproject_file=}, {verbose=}, {debug=}"
        )

        file_cli_input = get_cli_file_input(input_file)
        logger.debug(f"File CLI arguments:\n{file_cli_input}")

        prioritized_inputs = SomesyCLIConfig(**{**file_cli_input, **cli_inputs})
        set_logger(
            debug=prioritized_inputs.debug,
            verbose=prioritized_inputs.verbose,
            info=prioritized_inputs.show_info,
        )

        # check if there is at least one file to sync
        if prioritized_inputs.no_sync_pyproject and prioritized_inputs.no_sync_cff:
            raise ValueError(
                "No sync target is enabled, nothing to do. Probably you did not intend this?"
            )

        # if there is a cli output set, make no_sync to False
        if prioritized_inputs.cff_file is not None:
            prioritized_inputs.no_sync_cff = False
        if prioritized_inputs.pyproject_file is not None:
            prioritized_inputs.no_sync_pyproject = False

        logger.info("[bold green]Syncing project metadata...[/bold green]\n")

        # info output
        logger.info("Files to sync:")
        if not prioritized_inputs.no_sync_pyproject:
            logger.info(
                f"  - [italic]pyproject.toml[/italic]\t[grey]({pyproject_file})[/grey]"
            )

        if not prioritized_inputs.no_sync_cff:
            logger.info(f"  - [italic]CITATION.cff[/italic]\t[grey]({cff_file})[/grey]")
        if not prioritized_inputs.no_sync_codemeta:
            logger.info(
                f"  - [italic]codemeta.json[/italic]\t[grey]({codemeta_file})[/grey]"
            )

        # sync files
        sync_command(
            input_file=input_file,
            pyproject_file=prioritized_inputs.pyproject_file
            if not prioritized_inputs.no_sync_pyproject
            else None,
            cff_file=prioritized_inputs.cff_file
            if not prioritized_inputs.no_sync_cff
            else None,
            codemeta_file=prioritized_inputs.codemeta_file
            if not prioritized_inputs.no_sync_codemeta
            else None,
        )

        logger.info("[bold green]Syncing completed.[/bold green]")

    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)
