"""Sync selected metadata files with given input file."""
import logging
from pathlib import Path

from rich.pretty import pretty_repr

from somesy.cff.writer import CFF
from somesy.codemeta import update_codemeta
from somesy.core.models import ProjectMetadata, SomesyConfig, SomesyInput
from somesy.pyproject.writer import Pyproject
from somesy.package_json.writer import PackageJSON

logger = logging.getLogger("somesy")


def sync(somesy_input: SomesyInput):
    """Sync selected metadata files with given input file."""
    conf, metadata = somesy_input.config, somesy_input.project

    logger.debug(
        f"Project metadata: {pretty_repr(metadata.dict(exclude_defaults=True))}"
    )

    if not conf.no_sync_pyproject:
        _sync_python(metadata, conf.pyproject_file)

    if not conf.no_sync_cff:
        _sync_cff(metadata, conf.cff_file)

    if not conf.sync_package_json:
        _sync_package_json(metadata, conf.package_json_file)

    # NOTE: codemeta should always be last, it uses (some of) the other targets
    if not conf.no_sync_codemeta:
        _sync_codemeta(conf)


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


def _sync_package_json(
    metadata: ProjectMetadata,
    package_json_file: Path,
):
    """Sync package.json file using project metadata.

    Args:
        metadata (ProjectMetadata): project metadata to sync pyproject.toml file.
        package_json_file (Path, optional): package.json file path if wanted to be synced. Defaults to None.
    """
    logger.verbose("Loading package.json file.")
    package_json = PackageJSON(package_json_file)
    logger.verbose("Syncing package.json file.")
    package_json.sync(metadata)
    package_json.save()
    logger.verbose("Saved synced package.json file.\n")


def _sync_codemeta(conf: SomesyConfig):
    logger.verbose("Updating codemeta.json file.")
    if update_codemeta(conf):
        logger.verbose(f"New codemeta graph written to {conf.codemeta_file}.")
    else:
        logger.verbose(f"Codemeta graph unchanged, keeping old {conf.codemeta_file}.")
