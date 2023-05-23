"""Discover somesy related files and paths."""
import logging
from pathlib import Path
from typing import Optional

from .config import INPUT_FILES_ORDERED

logger = logging.getLogger("somesy")


def discover_input(input_file: Optional[str] = None) -> Optional[Path]:
    """Check given input file path. If not given, find somesy configuration file path from default list.

    Args:
        input_file (Optional[str], optional): somesy configuration file path. Defaults to None.

    Raises:
        FileNotFoundError: Raised if no somesy input file found from cli input or the defaults.

    Returns:
        Optional[Path]:  somesy configuration file path.
    """
    if input_file:
        p = Path(input_file)
        if p.is_file():
            logger.verbose(f"Using given {p} as somesy input file.")  # type: ignore
            return p
        else:
            logger.verbose(  # type: ignore
                f"Given input file {p} does not exist. Trying to find somesy input file from defaults."
            )
    for filename in INPUT_FILES_ORDERED:
        p = Path(filename)
        if p.is_file():
            logger.verbose(  # type: ignore
                f"Using {p} from default somesy config list as somesy input file."
            )
            return p
    raise FileNotFoundError("No somesy input file found.")
