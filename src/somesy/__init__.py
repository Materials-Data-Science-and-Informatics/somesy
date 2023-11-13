"""somesy package."""
import importlib_metadata
from typing import Optional
from typing_extensions import Final
import platform
from pathlib import Path
from os import environ

# Set version, it will use version from pyproject.toml if defined
__version__: Final[str] = importlib_metadata.version(__package__ or __name__)

# Set tmp dir for Windows
__tmp_dir__: Optional[str] = None

if platform.system() == "Windows":
    # create temp folder
    driver_letter = Path(__file__).drive
    temp_folder = Path(f"{driver_letter}//Temp")
    temp_folder.mkdir(parents=True, exist_ok=True)

    # resolve temp folder to absolute path
    resolved_temp_folder = str(temp_folder.resolve())
    __tmp_dir__ = resolved_temp_folder
    environ["TMPDIR"] = resolved_temp_folder
