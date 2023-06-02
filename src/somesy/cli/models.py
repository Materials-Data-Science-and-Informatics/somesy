"""Models for the CLI commands."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
