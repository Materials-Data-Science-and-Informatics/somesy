"""Somesy log configuration."""

import logging
from enum import Enum, auto
from typing import Optional

from rich.logging import RichHandler

logger = logging.getLogger("somesy")

VERBOSE: int = 15
"""Custom logging level between INFO and DEBUG."""


class SomesyLogLevel(Enum):
    """Somesy-specific log levels."""

    SILENT = auto()
    INFO = auto()
    VERBOSE = auto()
    DEBUG = auto()

    @staticmethod
    def from_flags(
        *,
        info: Optional[bool] = None,
        verbose: Optional[bool] = None,
        debug: Optional[bool] = None,
    ):
        """Convert CLI/config flags into a log level."""
        if debug:
            return SomesyLogLevel.DEBUG
        elif verbose:
            return SomesyLogLevel.VERBOSE
        elif info:
            return SomesyLogLevel.INFO
        return SomesyLogLevel.SILENT

    @staticmethod
    def to_logging(lv):
        """Convert a somesy log level into a logging log level."""
        if lv == SomesyLogLevel.SILENT:
            return logging.WARNING
        if lv == SomesyLogLevel.INFO:
            return logging.INFO
        if lv == SomesyLogLevel.VERBOSE:
            return VERBOSE
        if lv == SomesyLogLevel.DEBUG:
            return logging.DEBUG


_log_level: Optional[SomesyLogLevel] = None


def get_log_level() -> Optional[SomesyLogLevel]:
    """Return current user-defined log level."""
    return _log_level


def set_log_level(log_level: SomesyLogLevel) -> None:
    """Set the current log level."""
    global _log_level
    # update current somesy log level
    _log_level = log_level
    # (re-)init logging (rich formatter config depends on passed log level)
    init_log()
    # set the current logging log level
    logger.setLevel(SomesyLogLevel.to_logging(log_level))


def init_log():
    """Initialize logging (add VERBOSE log level and Rich formatter)."""
    _add_verbose_level()
    _init_rich_handler(get_log_level())


# ----


def _add_verbose_level():
    """Add a VERBOSE level to logging, if not already existing."""
    if isinstance(logging.getLevelName("VERBOSE"), int):
        return  # nothing to do

    # add the new level, if not defined yet
    logging.addLevelName(level=VERBOSE, levelName="VERBOSE")
    logger.propagate = False

    def verbose_print(self, message, *args, **kwargs):
        """Verbose logging level print function."""
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, message.format(args), (), **kwargs)

    setattr(logging.Logger, "verbose", verbose_print)  # noqa: B010
    logging.basicConfig(
        format="%(message)s",
        datefmt="",
    )


_rich_handler = None


def _init_rich_handler(log_level):
    """(Re-)initialize rich logging handler, based on current log level."""
    global _rich_handler
    debug = log_level == SomesyLogLevel.DEBUG

    if _rich_handler is not None:  # remove old handler
        logger.removeHandler(_rich_handler)

    # create and add new handler (based on log level)
    _rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=True,
        show_level=debug,
        show_path=debug,
        tracebacks_show_locals=debug,
        markup=True,
    )
    logger.addHandler(_rich_handler)
