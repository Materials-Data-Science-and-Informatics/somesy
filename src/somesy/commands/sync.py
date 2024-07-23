"""Sync selected metadata files with given input file."""

import logging
from pathlib import Path
from typing import Type

from rich.pretty import pretty_repr

from somesy.cff.writer import CFF
from somesy.codemeta import CodeMeta
from somesy.core.models import ProjectMetadata, SomesyInput
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
    metadata: ProjectMetadata, file: Path, writer_cls: Type[ProjectMetadataWriter]
):
    """Sync metadata to a file using the provided writer."""
    logger.verbose(f"Loading '{file.name}' ...")
    writer = writer_cls(file)
    logger.verbose(f"Syncing '{file.name}' ...")
    writer.sync(metadata)
    writer.save(file)
    logger.verbose(f"Saved synced '{file.name}'.\n")


def sync(somesy_input: SomesyInput):
    """Sync selected metadata files with given input file."""
    conf, metadata = somesy_input.config, somesy_input.project

    pp_metadata = pretty_repr(metadata.model_dump(exclude_defaults=True))
    logger.debug(f"Project metadata: {pp_metadata}")

    # update these only if they exist:

    if conf.pyproject_file.is_file() and not conf.no_sync_pyproject:
        _sync_file(metadata, conf.pyproject_file, Pyproject)

    if conf.package_json_file.is_file() and not conf.no_sync_package_json:
        _sync_file(metadata, conf.package_json_file, PackageJSON)

    if conf.julia_file.is_file() and not conf.no_sync_julia:
        _sync_file(metadata, conf.julia_file, Julia)

    if conf.fortran_file.is_file() and not conf.no_sync_fortran:
        _sync_file(metadata, conf.fortran_file, Fortran)

    if conf.pom_xml_file.is_file() and not conf.no_sync_pom_xml:
        _sync_file(metadata, conf.pom_xml_file, POM)

    if conf.mkdocs_file.is_file() and not conf.no_sync_mkdocs:
        _sync_file(metadata, conf.mkdocs_file, MkDocs)

    if conf.rust_file.is_file() and not conf.no_sync_rust:
        _sync_file(metadata, conf.rust_file, Rust)

    # create these by default if they are missing:
    if not conf.no_sync_cff:
        _sync_file(metadata, conf.cff_file, CFF)

    if not conf.no_sync_codemeta:
        _sync_file(metadata, conf.codemeta_file, CodeMeta)
