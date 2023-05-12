"""Sync CFF and pyproject.toml files using project metadata that resides in pyproject.toml."""
from pathlib import Path
from typing import Optional

from somesy.cff.core import CFF
from somesy.core.core import get_project_metadata
from somesy.pyproject.core import Pyproject


def sync_from_pyproject(
    pyproject_path: Path,
    cff_path: Optional[Path],
    create_cff: bool = True,
    create_pyproject: bool = True,
    dump: bool = True,
):
    """Sync CFF and pyproject.toml files using project metadata that resides in pyproject.toml.

    Args:
        pyproject_path (Path): pyproject file to read project metadata from.
        cff_path (Path, optional): CFF file path if wanted to be synced. Defaults to None.
        create_cff (bool, optional): Create CFF file if does not exist. Defaults to True.
        create_pyproject (bool, optional): Create Pyproject file if does not exist. Defaults to True.
        dump (bool, optional): Whether to write changes to files. Defaults to True.
    """
    metadata = get_project_metadata(pyproject_path)
    pyproject = Pyproject(pyproject_path, create_pyproject)
    cff = CFF(cff_path, create_cff) if cff_path else None

    # sync
    pyproject.sync(metadata)
    if cff:
        cff.sync(metadata)

    # dump
    if dump:
        pyproject.dump()
        if cff:
            cff.dump()
