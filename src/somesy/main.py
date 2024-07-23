"""Main entry point for the somesy CLI."""

import logging
import sys

import typer

from somesy import __version__
from somesy.cli import fill, init, sync
from somesy.core.log import SomesyLogLevel, init_log, set_log_level

app = typer.Typer()

logger = logging.getLogger("somesy")


@app.callback()
def version(value: bool):
    """Show somesy version and exit."""
    if value:
        typer.echo(f"somesy version: {__version__}")
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", help=version.__doc__, callback=version
    ),
    show_info: bool = typer.Option(
        None,
        "--info",
        "-v",
        help="Enable basic logging.",
    ),
    verbose: bool = typer.Option(
        None,
        "--verbose",
        "-vv",
        help="Enable verbose logging.",
    ),
    debug: bool = typer.Option(
        None,
        "--debug",
        "-vvv",
        help="Enable debug logging.",
    ),
):
    """General flags and arguments for somesy."""
    init_log()

    if sum(map(int, map(bool, [show_info, verbose, debug]))) > 1:
        typer.echo(
            "Only one of --info, --verbose or --debug may be set!", file=sys.stderr
        )
        raise typer.Exit(1)

    if show_info or verbose or debug:
        # NOTE: only explicitly setting log level if a flag is passed,
        # in order to distinguish from using the "default log level"
        # (needed to check if the user did override the log level as a CLI flag)
        set_log_level(
            SomesyLogLevel.from_flags(info=show_info, verbose=verbose, debug=debug)
        )


# add subcommands
app.add_typer(sync.app, name="sync")
app.add_typer(init.app, name="init")
app.add_typer(fill.app, name="fill")
