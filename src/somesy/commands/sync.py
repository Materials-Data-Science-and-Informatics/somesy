"""Sync CFF and pyproject.toml files using project metadata that resides in pyproject.toml."""
import logging
from pathlib import Path
from typing import Optional

from somesy.cff.core import CFF
from somesy.core.core import ProjectMetadata, get_project_metadata
from somesy.pyproject.core import Pyproject

logger = logging.getLogger("somesy")


def sync(
    input_file: Path,
    pyproject_file: Optional[Path] = None,
    create_pyproject: bool = True,
    cff_file: Optional[Path] = None,
    create_cff: bool = True,
):
    """Sync CFF and pyproject.toml files using project metadata that resides in pyproject.toml.

    Args:
        input_file (Path): input file path to read project metadata from.
        pyproject_file (Path, optional): pyproject file to read project metadata from.
        create_pyproject (bool, optional): Create Pyproject file if does not exist. Defaults to True.
        cff_file (Path, optional): CFF file path if wanted to be synced. Defaults to None.
        create_cff (bool, optional): Create CFF file if does not exist. Defaults to True.
    """
    metadata = get_project_metadata(input_file)
    logger.debug(f"Project metadata: {metadata}")

    if pyproject_file is not None:
        _sync_python(metadata, pyproject_file, create_pyproject)

    if cff_file is not None:
        _sync_cff(metadata, cff_file, create_cff)


def _sync_python(
    metadata: ProjectMetadata,
    pyproject_file: Optional[Path] = None,
    create_pyproject: bool = True,
):
    """Sync pyproject.toml file using project metadata.

    Args:
        metadata (ProjectMetadata): project metadata to sync pyproject.toml file.
        pyproject_file (Path, optional): pyproject file to read project metadata from.
        create_pyproject (bool, optional): Create Pyproject file if does not exist. Defaults to True.
    """
    logger.verbose("Loading pyproject.toml file.")  # type: ignore
    pyproject = Pyproject(pyproject_file, create_pyproject)
    logger.info("Syncing pyproject.toml file.")
    pyproject.sync(metadata)
    pyproject.dump()
    logger.info("Saved synced pyproject.toml file.\n")


def _sync_cff(
    metadata: ProjectMetadata,
    cff_file: Optional[Path] = None,
    create_cff: bool = True,
):
    """Sync CITATION.cff file using project metadata.

    Args:
        metadata (ProjectMetadata): project metadata to sync pyproject.toml file.
        cff_file (Path, optional): CFF file path if wanted to be synced. Defaults to None.
        create_cff (bool, optional): Create CFF file if does not exist. Defaults to True.
    """
    logger.verbose("Loading CITATION.cff file.")  # type: ignore
    cff = CFF(cff_file, create_cff)
    logger.info("Syncing CITATION.cff file.")
    cff.sync(metadata)
    cff.dump()
    logger.info("Saved synced CITATION.cff file.\n")
