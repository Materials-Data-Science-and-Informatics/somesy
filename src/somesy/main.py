"""Main entry point for the somesy CLI."""
import logging
import traceback
from pathlib import Path

import typer

from somesy import __version__
from somesy.commands import sync as sync_command
from somesy.core.discover import discover_input
from somesy.core.utils import set_logger

logger = logging.getLogger("somesy")
app = typer.Typer()


def version_callback(value: bool):
    """Print version information."""
    if value:
        typer.echo(f"somesy version: {__version__}")
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback),
):
    """Response for version information."""


@app.command()
def sync(
    input_file: Path = typer.Option(
        Path(".somesy.toml"),
        "--input-file",
        "-i",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Somesy input file path",
    ),
    no_sync_cff: bool = typer.Option(
        False,
        "--no-sync-cff",
        "-C",
        help="Do not sync CITATION.cff file",
    ),
    cff_file: Path = typer.Option(
        Path("CITATION.cff"),
        "--cff-file",
        "-c",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="CITATION.cff file path",
    ),
    no_sync_pyproject: bool = typer.Option(
        False,
        "--no-sync-pyproject",
        "-P",
        help="Do not sync pyproject.toml file",
    ),
    pyproject_file: Path = typer.Option(
        Path("pyproject.toml"),
        "--pyproject-file",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Existing pyproject.toml file path",
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
        False,
        "--show-info",
        "-s",
        help="Get basic output (somesy is quiet by default)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Debug output",
    ),
):
    """Sync project metadata input with metadata files."""
    set_logger(debug=debug, verbose=verbose, info=show_info)
    # at least one of the sync options must be enabled
    if no_sync_cff and no_sync_pyproject and no_sync_codemeta:
        logger.warning("No files are enabled for sync, nothing to do!")
        typer.Exit(code=0)

    logger.info("[bold green]Syncing project metadata...[/bold green]\n")
    logger.debug(
        f"""CLI arguments:
        {verbose=}, {debug=}
        {input_file=},
        {cff_file=}, {no_sync_cff=},
        {pyproject_file=}, {no_sync_pyproject=},
        {codemeta_file=}, {no_sync_codemeta=},
        """
    )

    try:
        # check if input file exists, if not, try to find it from default list
        input_file = discover_input(input_file)

        # info output
        logger.info("Files to sync:")
        if not no_sync_pyproject:
            logger.info(
                f"  - [italic]pyproject.toml[/italic]\t[grey]({pyproject_file})[/grey]"
            )
        if not no_sync_cff:
            logger.info(f"  - [italic]CITATION.cff[/italic]\t[grey]({cff_file})[/grey]")
        if not no_sync_codemeta:
            logger.info(
                f"  - [italic]codemeta.json[/italic]\t[grey]({codemeta_file})[/grey]"
            )

        # sync files
        sync_command(
            input_file=input_file,
            pyproject_file=pyproject_file if not no_sync_pyproject else None,
            cff_file=cff_file if not no_sync_cff else None,
            codemeta_file=codemeta_file if not no_sync_codemeta else None,
        )

    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)

    logger.info("[bold green]Syncing completed.[/bold green]")


if __name__ == "__main__":
    app()
