"""Discover somesy related files and paths."""
import logging
from pathlib import Path
from typing import Optional

from .config import INPUT_FILES_ORDERED

logger = logging.getLogger("somesy")


def discover_input(input_file: Optional[Path] = None) -> Path:
    """Check given input file path. If not given, find somesy configuration file path from default list.

    Args:
        input_file: somesy configuration file path. Defaults to None.

    Raises:
        FileNotFoundError: Raised if no somesy input file found from cli input or the defaults.

    Returns:
        somesy configuration file path.
    """
    if input_file:
        if input_file.is_file():
            logger.info(f"Using given {input_file} as somesy input file.")
            return input_file
        else:
            logger.verbose(
                f"Given input file {input_file} does not exist. Trying to find somesy input file from defaults."
            )
    for filename in INPUT_FILES_ORDERED:
        input_file = Path(filename)
        if input_file.is_file():
            logger.verbose(
                f"Using {input_file} from default somesy config list as somesy input file."
            )
            return input_file
    raise FileNotFoundError("No somesy input file found.")
