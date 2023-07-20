"""Utility functions for CLI commands."""
import logging
import traceback

import typer
import wrapt

logger = logging.getLogger("somesy")


@wrapt.decorator
def wrap_exceptions(wrapped, instance, args, kwargs):
    """Format and log exceptions for cli commands."""
    try:
        return wrapped(*args, **kwargs)

    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1) from e
