"""Sync command for somesy."""

import logging
from pathlib import Path

import typer

from somesy.commands import sync as sync_command
from somesy.commands.sync import SYNC_TARGETS
from somesy.core.models import SomesyInput

from .util import (
    existing_dir_arg_config,
    existing_file_arg_config,
    file_arg_config,
    resolved_somesy_input,
    wrap_exceptions,
)

logger = logging.getLogger("somesy")

app = typer.Typer()


@app.callback(invoke_without_command=True)
@wrap_exceptions
def sync(
    input_file: Path | None = typer.Option(
        None,
        "--input-file",
        "-i",
        help="Somesy input file path (default: .somesy.toml)",
        **file_arg_config,
    ),
    no_sync_pyproject: bool | None = typer.Option(
        None,
        "--no-sync-pyproject",
        "-P",
        help="Do not sync pyproject.toml file (default: False)",
    ),
    pyproject_file: list[Path] | None = typer.Option(
        None,
        "--pyproject-file",
        "-p",
        help="Existing pyproject.toml file path(s) (default: pyproject.toml)",
        **existing_file_arg_config,
    ),
    no_sync_package_json: bool | None = typer.Option(
        None,
        "--no-sync-package-json",
        "-J",
        help="Do not sync package.json file (default: False)",
    ),
    package_json_file: list[Path] | None = typer.Option(
        None,
        "--package-json-file",
        "-j",
        help="Existing package.json file path(s) (default: package.json)",
        **existing_file_arg_config,
    ),
    no_sync_julia: bool | None = typer.Option(
        None,
        "--no-sync-julia",
        "-L",
        help="Do not sync Project.toml (Julia) file (default: False)",
    ),
    julia_file: list[Path] | None = typer.Option(
        None,
        "--julia-file",
        "-l",
        help="Custom Project.toml (Julia) file path(s) (default: Project.toml)",
        **existing_file_arg_config,
    ),
    no_sync_fortran: bool | None = typer.Option(
        None,
        "--no-sync-fortran",
        "-F",
        help="Do not sync fpm.toml (Fortran) file (default: False)",
    ),
    fortran_file: list[Path] | None = typer.Option(
        None,
        "--fortran-file",
        "-f",
        help="Custom fpm.toml (Fortran) file path(s) (default: fpm.toml)",
        **existing_file_arg_config,
    ),
    no_sync_pom_xml: bool | None = typer.Option(
        None,
        "--no-sync-pomxml",
        "-X",
        help="Do not sync pom.xml (Java Maven) file (default: False)",
    ),
    pom_xml_file: list[Path] | None = typer.Option(
        None,
        "--pomxml-file",
        "-x",
        help="Custom pom.xml (Java Maven) file path(s) (default: pom.xml)",
        **existing_file_arg_config,
    ),
    no_sync_mkdocs: bool | None = typer.Option(
        None,
        "--no-sync-mkdocs",
        "-D",
        help="Do not sync mkdocs.yml file (default: False)",
    ),
    mkdocs_file: list[Path] | None = typer.Option(
        None,
        "--mkdocs-file",
        "-d",
        help="Custom mkdocs.yml file path(s) (default: mkdocs.yml)",
        **existing_file_arg_config,
    ),
    no_sync_rust: bool | None = typer.Option(
        None,
        "--no-sync-rust",
        "-R",
        help="Do not sync Cargo.toml file (default: False)",
    ),
    rust_file: list[Path] | None = typer.Option(
        None,
        "--rust-file",
        "-r",
        help="Custom Cargo.toml file path(s) (default: Cargo.toml)",
        **existing_file_arg_config,
    ),
    no_sync_cff: bool | None = typer.Option(
        None,
        "--no-sync-cff",
        "-C",
        help="Do not sync CITATION.cff file (default: False)",
    ),
    cff_file: list[Path] | None = typer.Option(
        None,
        "--cff-file",
        "-c",
        help="CITATION.cff file path(s) (default: CITATION.cff)",
        **file_arg_config,
    ),
    no_sync_codemeta: bool | None = typer.Option(
        None,
        "--no-sync-codemeta",
        "-M",
        help="Do not sync codemeta.json file (default: False)",
    ),
    codemeta_file: list[Path] | None = typer.Option(
        None,
        "--codemeta-file",
        "-m",
        help="Custom codemeta.json file path(s) (default: codemeta.json)",
        **file_arg_config,
    ),
    merge_codemeta: bool | None = typer.Option(
        False,
        "--merge/--overwrite",
        help="Merge codemeta.json with with an existing codemeta.json file (default: False)",
    ),
    pass_validation: bool | None = typer.Option(
        False,
        "--pass-validation",
        "-V",
        help="Allow incomplete input and pass output validation (default: False)",
    ),
    packages: list[Path] | None = typer.Option(
        None,
        "--packages",
        "-k",
        help="Packages (subfolders) for monorepos with their own somesy config.",
        **existing_dir_arg_config,
    ),
):
    """Sync project metadata input with metadata files."""
    somesy_input = resolved_somesy_input(
        input_file=input_file,
        no_sync_cff=no_sync_cff,
        cff_file=cff_file,
        no_sync_pyproject=no_sync_pyproject,
        pyproject_file=pyproject_file,
        no_sync_package_json=no_sync_package_json,
        package_json_file=package_json_file,
        no_sync_codemeta=no_sync_codemeta,
        codemeta_file=codemeta_file,
        no_sync_julia=no_sync_julia,
        julia_file=julia_file,
        no_sync_fortran=no_sync_fortran,
        fortran_file=fortran_file,
        no_sync_pom_xml=no_sync_pom_xml,
        pom_xml_file=pom_xml_file,
        no_sync_mkdocs=no_sync_mkdocs,
        mkdocs_file=mkdocs_file,
        no_sync_rust=no_sync_rust,
        rust_file=rust_file,
        merge_codemeta=merge_codemeta,
        pass_validation=pass_validation,
        packages=packages,
    )

    run_sync(somesy_input)


def run_sync(somesy_input: SomesyInput):
    """Write log messages and run synchronization based on passed config."""
    conf = somesy_input.config
    logger.info("[bold green]Synchronizing project metadata...[/bold green]")
    logger.info("Files to sync:")
    for target in SYNC_TARGETS:
        if not getattr(conf, f"no_sync_{target.key}"):
            files = getattr(conf, f"{target.key}_file")
            gap = "\n" if target.log_gap else ""
            logger.info(
                f"  - [italic]{target.label}[/italic]:\t[grey]{files}[/grey]{gap}"
            )
    # ----
    if conf.pass_validation:
        logger.info("[bold yellow]Passing validation of metadata files.[/bold yellow]")
    sync_command(somesy_input)
    # ----
    logger.info("[bold green]Metadata synchronization completed.[/bold green]")
