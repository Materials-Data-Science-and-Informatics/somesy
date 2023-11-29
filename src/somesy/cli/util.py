"""Utility functions for CLI commands."""
import logging
import traceback
from typing import Optional

import typer
import wrapt
from rich.pretty import pretty_repr

from somesy.core.core import discover_input
from somesy.core.log import SomesyLogLevel, get_log_level, set_log_level
from somesy.core.models import SomesyConfig, SomesyInput

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


def resolved_somesy_input(**cli_args) -> SomesyInput:
    """Return a combined `SomesyInput` based on config file and passed CLI args.

    Will also adjust log levels accordingly.
    """
    # figure out what input file to use
    input_file = discover_input(cli_args.pop("input_file", None))

    # create config based on passed arguments
    passed_args = {k: v for k, v in cli_args.items() if v is not None}
    somesy_conf = SomesyConfig(input_file=input_file, **passed_args)

    # cli_log_level is None if the user did not pass a log level (-> "default")
    cli_log_level: Optional[SomesyLogLevel] = get_log_level()

    if cli_log_level is not None:
        # update log level flags if cli log level was set
        somesy_conf.update_log_level(cli_log_level)

    somesy_input: SomesyInput = somesy_conf.get_input()

    if cli_log_level is None:
        # no cli log level -> set it according to the loaded configuration
        set_log_level(somesy_input.config.log_level())

    logger.debug(
        f"Combined config (Defaults + File + CLI):\n{pretty_repr(somesy_input.config)}"
    )
    return somesy_input
