"""Somesy log configuration."""

import logging
from enum import Enum, auto

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
        info: bool | None = None,
        verbose: bool | None = None,
        debug: bool | None = None,
    ):
        """Convert CLI/config flags into a log level.

        If several flags are set, the most verbose level wins (with a warning).
        """
        if sum(map(int, map(bool, [info, verbose, debug]))) > 1:
            logger.warning(
                "More than one of info, verbose and debug log flags is set, "
                "using the most verbose one."
            )
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
        raise ValueError(f"Unsupported log level: {lv}")


_log_level: SomesyLogLevel | None = None


def get_log_level() -> SomesyLogLevel | None:
    """Return current user-defined log level."""
    return _log_level


def reset_log_level() -> None:
    """Forget the explicitly set (CLI) log level, e.g. at the start of an invocation."""
    global _log_level
    _log_level = None


def set_log_level(log_level: SomesyLogLevel) -> None:
    """Set the current log level (and remember it as explicitly set)."""
    global _log_level
    _log_level = log_level
    apply_log_level(log_level)


def apply_log_level(log_level: SomesyLogLevel) -> None:
    """Apply a log level to logging without recording it as explicitly set."""
    # (re-)init logging (rich formatter config depends on passed log level)
    init_log(log_level)
    # set the current logging log level
    logger.setLevel(SomesyLogLevel.to_logging(log_level))


def init_log(log_level: SomesyLogLevel | None = None):
    """Initialize logging (add VERBOSE log level and Rich formatter)."""
    _add_verbose_level()
    _init_rich_handler(log_level or get_log_level())


# ----


def _add_verbose_level():
    """Add a VERBOSE level to logging (idempotent) and configure the logger."""
    logging.addLevelName(level=VERBOSE, levelName="VERBOSE")
    # the rich handler handles output; propagate so that e.g. pytest's caplog works
    logger.propagate = True


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
