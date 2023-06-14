"""Main entry point for the somesy CLI."""

import typer

from somesy import __version__
from somesy.cli import init, sync

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


# add subcommands
app.add_typer(sync.app, name="sync")
app.add_typer(init.app, name="init")

if __name__ == "__main__":
    app()
