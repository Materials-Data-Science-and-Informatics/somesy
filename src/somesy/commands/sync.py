"""Sync selected metadata files with given input file."""

import json
import logging
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import ValidationError
from rich.markup import escape
from rich.pretty import pretty_repr

from somesy.cff.writer import CFF
from somesy.codemeta import CodeMeta
from somesy.codemeta.enrich import enrich as enrich_codemeta
from somesy.core.core import INPUT_FILES_ORDERED
from somesy.core.log import VERBOSE
from somesy.core.models import ProjectMetadata, SomesyConfig, SomesyInput
from somesy.core.writer import ProjectMetadataWriter
from somesy.fortran.writer import Fortran
from somesy.julia.writer import Julia
from somesy.mkdocs import MkDocs
from somesy.package_json.writer import PackageJSON
from somesy.pom_xml.writer import POM
from somesy.pom_xml.xmlproxy import XMLProxy
from somesy.pyproject.writer import Pyproject
from somesy.rust import Rust

logger = logging.getLogger("somesy")


class SyncTarget(NamedTuple):
    """A metadata file type that somesy can sync.

    The config attributes are `no_sync_<key>` and `<key>_file`.
    """

    key: str
    writer: type[Any]  # a ProjectMetadataWriter subclass
    label: str  # name shown in the CLI log
    create_if_missing: bool = False  # create the file if it does not exist
    codemeta_source: bool = False  # enriches codemeta.json under the same key
    log_gap: bool = False  # CLI log: blank line after this entry


# in sync order
SYNC_TARGETS = [
    SyncTarget("pyproject", Pyproject, "pyproject.toml", codemeta_source=True),
    SyncTarget("package_json", PackageJSON, "package.json", codemeta_source=True),
    SyncTarget("julia", Julia, "Project.toml", codemeta_source=True, log_gap=True),
    SyncTarget("fortran", Fortran, "fpm.toml(fortran)", codemeta_source=True),
    SyncTarget("pom_xml", POM, "pom.xml", codemeta_source=True, log_gap=True),
    SyncTarget("mkdocs", MkDocs, "mkdocs.yml"),
    SyncTarget("rust", Rust, "Cargo.toml", codemeta_source=True),
    SyncTarget("cff", CFF, "CITATION.cff", create_if_missing=True),
    SyncTarget(
        "codemeta", CodeMeta, "codemeta.json", create_if_missing=True, log_gap=True
    ),
]


def _semantic_data(data: Any) -> Any:
    """Return format-neutral data without formatting trivia."""
    if isinstance(data, XMLProxy):
        xml = ET.tostring(data._node, encoding="unicode")
        return ET.canonicalize(xml, strip_text=True)
    if unwrap := getattr(data, "unwrap", None):
        data = unwrap()
    if isinstance(data, Mapping):
        return {key: _semantic_data(value) for key, value in data.items()}
    if isinstance(data, (list, tuple)):
        return [_semantic_data(value) for value in data]
    return data


def _sync_file(
    metadata: ProjectMetadata,
    file: Path,
    writer_cls: type[ProjectMetadataWriter],
    merge_codemeta: bool | None = False,
    pass_validation: bool | None = False,
    codemeta_sources: dict[str, Path | list[Path] | None] | None = None,
    codemeta_root: Path | None = None,
    codemeta_project_root: Path | None = None,
):
    """Sync metadata to a file using the provided writer."""
    logger.log(VERBOSE, f"Loading '{file.name}' ...")
    existed = file.exists()
    if writer_cls == CodeMeta:
        writer: ProjectMetadataWriter = writer_cls(
            file, merge=merge_codemeta, pass_validation=pass_validation
        )
    else:
        writer = writer_cls(file, pass_validation=pass_validation)
    logger.log(VERBOSE, f"Syncing '{file.name}' ...")
    original_data = _semantic_data(writer._data)
    if writer_cls == CodeMeta and existed:
        # the writer may already have upgraded a legacy file in memory:
        # compare against what is actually on disk
        try:
            original_data = _semantic_data(json.loads(file.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    writer.sync(metadata)
    if writer_cls == CodeMeta and codemeta_sources is not None:
        root = codemeta_root or file.parent
        enrich_codemeta(
            writer._data, codemeta_sources, root, codemeta_project_root or root
        )
    if not existed or _semantic_data(writer._data) != original_data:
        writer.save(file)
        logger.log(VERBOSE, f"Saved synced '{file.name}'.\n")


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


def _describe_error(error: Exception) -> str:
    """Return a short one-line description of a package loading error."""
    if isinstance(error, ValidationError):
        return "; ".join(
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
            for err in error.errors()
        )
    return str(error) or type(error).__name__


def sync(
    somesy_input: SomesyInput,
    is_package: bool = False,
    project_root: Path | None = None,
):
    """Sync selected metadata files with given input file.

    Args:
        somesy_input: The input configuration and metadata to sync
        is_package: Whether this is a package (subfolder) being synced
        project_root: Root of the overall project, differs from the base
            directory for packages of a multi-package repository. Files shared
            by all packages, such as a lock file, are looked up from here.

    """
    conf, metadata = somesy_input.config, somesy_input.project

    # Get the base directory from the input file's location
    if somesy_input._origin is None:
        logger.warning(
            "No origin found for somesy input, using current working directory."
        )
        base_dir = Path.cwd()
    else:
        base_dir = somesy_input._origin.parent

    # Resolve all paths in the config relative to the base directory
    conf.resolve_paths(base_dir)

    if is_package:
        logger.info("\n[bold green]Synchronizing package metadata...[/bold green]")
    else:
        logger.info("\n[bold green]Synchronizing root project metadata...[/bold green]")

    pp_metadata = pretty_repr(metadata.model_dump(exclude_defaults=True))
    logger.debug(f"Project metadata: {pp_metadata}")

    # First sync the current project
    _sync_root_project(conf, metadata, base_dir, project_root or base_dir)

    # Then sync each package if defined
    if conf.packages:
        packages = [conf.packages] if isinstance(conf.packages, Path) else conf.packages
        skipped: list[Path] = []
        for package in packages:
            logger.info(f"\n[bold blue]Processing package {package}...[/bold blue]")

            # Try all possible input files in order of priority
            config_files = [package / file for file in INPUT_FILES_ORDERED]
            package_input = None
            config_file: Path | None = None
            load_error: Exception | None = None

            for config_file in config_files:
                try:
                    package_input = SomesyInput.from_input_file(
                        config_file, allow_incomplete=bool(conf.pass_validation)
                    )
                    logger.debug(f"Found config file: {config_file}")
                    break
                except (FileNotFoundError, RuntimeError):
                    continue
                except (ValueError, KeyError, OSError) as error:  # invalid config
                    load_error = error
                    break

            if package_input is None:
                if load_error is not None:
                    logger.warning(
                        f"Skipping package {package}: cannot load '{config_file}': "
                        f"{escape(_describe_error(load_error))}"
                    )
                else:
                    logger.warning(
                        f"No valid somesy config found in package {package} "
                        f"(tried: {', '.join(str(f) for f in config_files)})"
                    )
                skipped.append(package)
                continue

            # The package's own config is the base; only options explicitly
            # passed on the root CLI override it (nothing is inherited from the
            # root config file or defaults).
            cli_overrides = {
                key: value
                for key, value in conf._cli_overrides.items()
                if key.startswith("no_sync_")
                or key in ("merge_codemeta", "pass_validation")
            }
            package_input.config = SomesyConfig(
                **{
                    **package_input.config.model_dump(),
                    **cli_overrides,
                    "input_file": config_file,
                    "packages": None,  # avoid recursive package handling
                }
            )

            # CFF and CodeMeta paths are resolved relative to the package
            # directory; unset ones fall back to the config defaults.

            # Recursively call sync on the package
            sync(
                package_input,
                is_package=True,
                project_root=project_root or base_dir,
            )

        if skipped:
            logger.warning(
                f"Skipped {len(skipped)} package(s) that could not be loaded: "
                f"{', '.join(str(p) for p in skipped)}"
            )


def _sync_root_project(
    conf: SomesyConfig,
    metadata: ProjectMetadata,
    base_dir: Path,
    project_root: Path,
) -> None:
    """Sync metadata files for the root project."""
    for target in SYNC_TARGETS:
        if getattr(conf, f"no_sync_{target.key}"):
            continue
        files = getattr(conf, f"{target.key}_file")
        # targets that are not created by default are updated only if they exist
        if not (files or target.create_if_missing):
            continue
        kwargs: dict[str, Any] = {}
        if target.writer is CodeMeta:
            kwargs = {
                "merge_codemeta": conf.merge_codemeta,
                "codemeta_root": base_dir,
                "codemeta_project_root": project_root,
                "codemeta_sources": {
                    t.key: (
                        None
                        if getattr(conf, f"no_sync_{t.key}")
                        else getattr(conf, f"{t.key}_file")
                    )
                    for t in SYNC_TARGETS
                    if t.codemeta_source
                },
            }
        _sync_files(
            metadata,
            files,
            target.writer,
            create_if_missing=target.create_if_missing,
            pass_validation=conf.pass_validation,
            **kwargs,
        )
