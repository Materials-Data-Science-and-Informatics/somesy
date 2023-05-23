"""Sync selected metadata files with given input file."""
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
    cff_file: Optional[Path] = None,
    create_cff: bool = True,
):
    """Sync selected metadata files with given input file.

    Args:
        input_file (Path): input file path to read project metadata from.
        pyproject_file (Path, optional): pyproject file to read project metadata from.
        cff_file (Path, optional): CFF file path if wanted to be synced. Defaults to None.
        create_cff (bool, optional): Create CFF file if does not exist. Defaults to True.
    """
    metadata = get_project_metadata(input_file)
    logger.debug(f"Project metadata: {metadata}")

    if pyproject_file is not None:
        _sync_python(metadata, pyproject_file)

    if cff_file is not None:
        _sync_cff(metadata, cff_file, create_cff)


def _sync_python(
    metadata: ProjectMetadata,
    pyproject_file: Optional[Path] = None,
):
    """Sync pyproject.toml file using project metadata.

    Args:
        metadata (ProjectMetadata): project metadata to sync pyproject.toml file.
        pyproject_file (Path, optional): pyproject file to read project metadata from.
    """
    logger.verbose("Loading pyproject.toml file.")  # type: ignore
    pyproject = Pyproject(pyproject_file)
    logger.verbose("Syncing pyproject.toml file.")  # type: ignore
    pyproject.sync(metadata)
    pyproject.save()
    logger.verbose("Saved synced pyproject.toml file.\n")  # type: ignore


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
    logger.verbose("Syncing CITATION.cff file.")  # type: ignore
    cff.sync(metadata)
    cff.save()
    logger.verbose("Saved synced CITATION.cff file.\n")  # type: ignore
