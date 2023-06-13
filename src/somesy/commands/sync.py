"""Sync selected metadata files with given input file."""
import logging
from pathlib import Path
from typing import Optional

from rich.pretty import pretty_repr

from somesy.cff.core import CFF
from somesy.codemeta import update_codemeta
from somesy.core.core import ProjectMetadata, get_project_metadata
from somesy.pyproject.core import Pyproject

logger = logging.getLogger("somesy")


def sync(
    input_file: Path,
    pyproject_file: Optional[Path] = None,
    cff_file: Optional[Path] = None,
    codemeta_file: Optional[Path] = None,
):
    """Sync selected metadata files with given input file.

    Args:
        input_file (Path): input file path to read project metadata from.
        pyproject_file (Path, optional): pyproject file to read project metadata from.
        cff_file (Path, optional): CFF file path if wanted to be synced. Defaults to None.
        codemeta_file (Path, optional): codemeta file path if wanted to be synced. Defaults to None.
    """
    metadata = get_project_metadata(input_file)
    logger.debug(
        f"Project metadata: {pretty_repr(metadata.dict(exclude_defaults=True))}"
    )

    if pyproject_file is not None:
        _sync_python(metadata, pyproject_file)

    if cff_file is not None:
        _sync_cff(metadata, cff_file)

    # NOTE: codemeta should always be last, it uses (some of) the other targets
    if codemeta_file is not None:
        update_codemeta(codemeta_file, cff_file)


def _sync_python(
    metadata: ProjectMetadata,
    pyproject_file: Path,
):
    """Sync pyproject.toml file using project metadata.

    Args:
        metadata (ProjectMetadata): project metadata to sync pyproject.toml file.
        pyproject_file (Path, optional): pyproject file to read project metadata from.
    """
    logger.verbose("Loading pyproject.toml file.")
    pyproject = Pyproject(pyproject_file)
    logger.verbose("Syncing pyproject.toml file.")
    pyproject.sync(metadata)
    pyproject.save()
    logger.verbose("Saved synced pyproject.toml file.\n")


def _sync_cff(
    metadata: ProjectMetadata,
    cff_file: Path,
):
    """Sync CITATION.cff file using project metadata.

    Args:
        metadata (ProjectMetadata): project metadata to sync pyproject.toml file.
        cff_file (Path, optional): CFF file path if wanted to be synced. Defaults to None.
    """
    logger.verbose("Loading CITATION.cff file.")
    cff = CFF(cff_file)
    logger.verbose("Syncing CITATION.cff file.")
    cff.sync(metadata)
    cff.save()
    logger.verbose("Saved synced CITATION.cff file.\n")
