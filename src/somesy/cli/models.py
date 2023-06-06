"""Models for the CLI commands."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SyncCommandOptions:
    """Dataclass for sync command options."""

    input_file: Optional[Path] = None
    no_sync_cff: Optional[bool] = None
    cff_file: Optional[Path] = None
    no_sync_pyproject: Optional[bool] = None
    pyproject_file: Optional[Path] = None
    show_info: Optional[bool] = None
    verbose: Optional[bool] = None
    debug: Optional[bool] = None

    def asdict(self, remove_keys: Optional[List[str]] = None):
        """Remove None values from dict and return absolute paths for Path objects."""
        if remove_keys is None:
            remove_keys = []

        response = {}
        for key, value in self.__dict__.items():
            if key in remove_keys or value is None:
                continue
            else:
                response[key] = value
        return response
