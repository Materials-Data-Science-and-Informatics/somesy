"""somesy package."""
import platform
from os import environ
from pathlib import Path
from typing import Optional

import importlib_metadata
from typing_extensions import Final

# Set version, it will use version from pyproject.toml if defined
__version__: Final[str] = importlib_metadata.version(__package__ or __name__)

# Set tmp dir for Windows
__tmp_dir__: Optional[str] = None
__tmp_codemeta_dir__: Optional[str] = None

if platform.system() == "Windows":
    # create temp folder
    root_path = Path(__file__).parent.parent.parent
    temp_folder = Path(f"{root_path.resolve()}//Temp")
    temp_folder.mkdir(exist_ok=True)

    # resolve temp folder to absolute path
    resolved_temp_folder = str(temp_folder.resolve())
    __tmp_dir__ = resolved_temp_folder
    environ["TMPDIR"] = resolved_temp_folder

    # create temp folder for codemeta
    codemeta_folder = Path(f"{temp_folder}//codemeta")
    codemeta_folder.mkdir(exist_ok=True)
    __tmp_codemeta_dir__ = str(codemeta_folder.resolve())
