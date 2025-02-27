"""Sync selected metadata files with given input file."""

import logging
from pathlib import Path
from typing import Optional, Type

from rich.pretty import pretty_repr

from somesy.cff.writer import CFF
from somesy.codemeta import CodeMeta
from somesy.core.core import INPUT_FILES_ORDERED
from somesy.core.models import ProjectMetadata, SomesyConfig, SomesyInput
from somesy.core.writer import ProjectMetadataWriter
from somesy.fortran.writer import Fortran
from somesy.julia.writer import Julia
from somesy.mkdocs import MkDocs
from somesy.package_json.writer import PackageJSON
from somesy.pom_xml.writer import POM
from somesy.pyproject.writer import Pyproject
from somesy.rust import Rust

logger = logging.getLogger("somesy")


def _sync_file(
    metadata: ProjectMetadata,
    file: Path,
    writer_cls: Type[ProjectMetadataWriter],
    merge_codemeta: Optional[bool] = False,
    pass_validation: Optional[bool] = False,
):
    """Sync metadata to a file using the provided writer."""
    logger.verbose(f"Loading '{file.name}' ...")
    if writer_cls == CodeMeta:
        writer = writer_cls(file, merge=merge_codemeta, pass_validation=pass_validation)
    else:
        writer = writer_cls(file, pass_validation=pass_validation)
    logger.verbose(f"Syncing '{file.name}' ...")
    writer.sync(metadata)
    writer.save(file)
    logger.verbose(f"Saved synced '{file.name}'.\n")


def _sync_files(
    metadata, files, writer_class, create_if_missing: bool = False, **kwargs
):
    """Sync metadata to files using the provided writer.

    Args:
        metadata: Project metadata to sync
        files: Path or list of paths to sync
        writer_class: Writer class to use
        create_if_missing: Whether to create the file if it doesn't exist
        **kwargs: Additional arguments passed to the writer

    """
    if isinstance(files, Path):
        files = [files]
    for file in files:
        if file.is_file() or create_if_missing:
            _sync_file(metadata, file, writer_class, **kwargs)


def sync(somesy_input: SomesyInput, is_package: bool = False):
    """Sync selected metadata files with given input file.

    Args:
        somesy_input: The input configuration and metadata to sync
        is_package: Whether this is a package (subfolder) being synced

    """
    conf, metadata = somesy_input.config, somesy_input.project

    # Get the base directory from the input file's location
    try:
        base_dir = somesy_input._origin.parent
    except AttributeError:
        logger.warning(
            "No origin found for somesy input, using current working directory."
        )
        base_dir = Path.cwd()

    # Resolve all paths in the config relative to the base directory
    conf.resolve_paths(base_dir)

    if is_package:
        logger.info("\n[bold green]Synchronizing package metadata...[/bold green]")
    else:
        logger.info("\n[bold green]Synchronizing root project metadata...[/bold green]")

    pp_metadata = pretty_repr(metadata.model_dump(exclude_defaults=True))
    logger.debug(f"Project metadata: {pp_metadata}")

    # First sync the current project
    _sync_root_project(conf, metadata)

    # Then sync each package if defined
    if conf.packages:
        packages = [conf.packages] if isinstance(conf.packages, Path) else conf.packages
        for package in packages:
            logger.info(f"\n[bold blue]Processing package {package}...[/bold blue]")

            # Try all possible input files in order of priority
            config_files = [package / file for file in INPUT_FILES_ORDERED]
            package_input = None

            for config_file in config_files:
                try:
                    package_input = SomesyInput.from_input_file(config_file)
                    logger.debug(f"Found config file: {config_file}")
                    break
                except (FileNotFoundError, RuntimeError):
                    continue

            if package_input is None:
                logger.warning(
                    f"No valid somesy config found in package {package} "
                    f"(tried: {', '.join(str(f) for f in config_files)})"
                )
                continue

            # Create new config with CLI options and package's input file
            cli_options = {
                "no_sync_pyproject": conf.no_sync_pyproject,
                "no_sync_package_json": conf.no_sync_package_json,
                "no_sync_julia": conf.no_sync_julia,
                "no_sync_fortran": conf.no_sync_fortran,
                "no_sync_pom_xml": conf.no_sync_pom_xml,
                "no_sync_mkdocs": conf.no_sync_mkdocs,
                "no_sync_rust": conf.no_sync_rust,
                "no_sync_cff": conf.no_sync_cff,
                "no_sync_codemeta": conf.no_sync_codemeta,
                "merge_codemeta": conf.merge_codemeta,
                "pass_validation": conf.pass_validation,
                "packages": None,  # Don't pass packages to avoid recursive package handling
            }
            package_input.config = SomesyConfig(input_file=config_file, **cli_options)

            # Set default CFF and CodeMeta paths in package directory if not specified
            if not package_input.config.no_sync_cff:
                package_input.config.cff_file = Path("CITATION.cff")
            if not package_input.config.no_sync_codemeta:
                package_input.config.codemeta_file = Path("codemeta.json")

            # Recursively call sync on the package
            sync(package_input, is_package=True)


def _sync_root_project(conf: SomesyConfig, metadata: ProjectMetadata):
    """Sync metadata files for the root project."""
    # update these only if they exist:
    if conf.pyproject_file and not conf.no_sync_pyproject:
        _sync_files(
            metadata,
            conf.pyproject_file,
            Pyproject,
            pass_validation=conf.pass_validation,
        )

    if conf.package_json_file and not conf.no_sync_package_json:
        _sync_files(
            metadata,
            conf.package_json_file,
            PackageJSON,
            pass_validation=conf.pass_validation,
        )

    if conf.julia_file and not conf.no_sync_julia:
        _sync_files(
            metadata,
            conf.julia_file,
            Julia,
            pass_validation=conf.pass_validation,
        )

    if conf.fortran_file and not conf.no_sync_fortran:
        _sync_files(
            metadata,
            conf.fortran_file,
            Fortran,
            pass_validation=conf.pass_validation,
        )

    if conf.pom_xml_file and not conf.no_sync_pom_xml:
        _sync_files(
            metadata,
            conf.pom_xml_file,
            POM,
            pass_validation=conf.pass_validation,
        )

    if conf.mkdocs_file and not conf.no_sync_mkdocs:
        _sync_files(
            metadata,
            conf.mkdocs_file,
            MkDocs,
            pass_validation=conf.pass_validation,
        )

    if conf.rust_file and not conf.no_sync_rust:
        _sync_files(
            metadata,
            conf.rust_file,
            Rust,
            pass_validation=conf.pass_validation,
        )

    # create these by default if they are missing:
    if not conf.no_sync_cff:
        _sync_files(
            metadata,
            conf.cff_file,
            CFF,
            create_if_missing=True,
            pass_validation=conf.pass_validation,
        )

    if not conf.no_sync_codemeta:
        _sync_files(
            metadata,
            conf.codemeta_file,
            CodeMeta,
            create_if_missing=True,
            merge_codemeta=conf.merge_codemeta,
            pass_validation=conf.pass_validation,
        )
