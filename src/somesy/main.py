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
    try:
        set_logger(debug=debug, verbose=verbose)
        logger.info("[bold green]Syncing project metadata...[/bold green]\n")
        logger.debug(
            f"CLI arguments:\n{input_file=}, {no_sync_cff=}, {cff_file=}, {no_sync_pyproject=}, {pyproject_file=}, {verbose=}, {debug=}"
        )

        # at least one of the sync options must be False
        if no_sync_cff and no_sync_pyproject:
            raise ValueError("There should be at least one file to sync.")

        # check if input file exists, if not, try to find it from default list
        input_file = discover_input(str(input_file) if input_file else None)

        # verbose output
        logger.verbose("Files to sync:")  # type: ignore
        logger.verbose(  # type: ignore
            f"  - [italic]Pyproject.toml[/italic] [grey]({pyproject_file})[/grey]"
        )

        if cff_file:
            logger.verbose(  # type: ignore
                f"  - [italic]CITATION.cff[/italic] [grey]({cff_file})[/grey]"
            )
        logger.verbose("\n")  # type: ignore

        # sync files
        sync_command(
            input_file=input_file,
            pyproject_file=Path(pyproject_file) if pyproject_file else None,
            cff_file=Path(cff_file) if cff_file else None,
        )

        logger.info("[bold green]Syncing completed.[/bold green]")
    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
