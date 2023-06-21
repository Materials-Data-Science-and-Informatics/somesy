"""Utility functions for somesy."""
import logging

from rich.logging import RichHandler

from somesy.core.config import VERBOSE

logger = logging.getLogger("somesy")


def set_logger(
    *, debug: bool = False, verbose: bool = False, info: bool = False
) -> None:
    """Set logger to rich handler and add custom logging level.

    If no flag is set, will be mostly silent (only warnings and errors).

    Args:
        debug (bool): Debug mode, overrides verbose and info modes.
        verbose (bool): Verbose mode, overrides info mode.
        info (bool): Prints basic output (instead of being silent).
    """
    logging.addLevelName(level=VERBOSE, levelName="VERBOSE")
    logger.propagate = False

    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(VERBOSE)
    elif info:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    def verbose_print(self, message, *args, **kwargs):
        """Verbose logging level print function."""
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, message.format(args), (), **kwargs)

    setattr(logging.Logger, "verbose", verbose_print)  # noqa: B010
    logging.basicConfig(
        format="%(message)s",
        datefmt="",
    )
    if not logger.handlers:
        logger.addHandler(
            RichHandler(
                show_time=False,
                rich_tracebacks=True,
                show_level=debug,
                show_path=debug,
                tracebacks_show_locals=debug,
                markup=True,
            )
        )
