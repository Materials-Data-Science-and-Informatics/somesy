"""Sync command for somesy."""

import logging
from pathlib import Path
from typing import List, Optional

import typer

from somesy.commands import sync as sync_command
from somesy.core.models import SomesyInput

from .util import (
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
    input_file: Optional[Path] = typer.Option(
        None,
        "--input-file",
        "-i",
        help="Somesy input file path (default: .somesy.toml)",
        **file_arg_config,
    ),
    no_sync_pyproject: Optional[bool] = typer.Option(
        None,
        "--no-sync-pyproject",
        "-P",
        help="Do not sync pyproject.toml file (default: False)",
    ),
    pyproject_file: Optional[List[Path]] = typer.Option(
        None,
        "--pyproject-file",
        "-p",
        help="Existing pyproject.toml file path(s) (default: pyproject.toml)",
        **existing_file_arg_config,
    ),
    no_sync_package_json: Optional[bool] = typer.Option(
        None,
        "--no-sync-package-json",
        "-J",
        help="Do not sync package.json file (default: False)",
    ),
    package_json_file: Optional[List[Path]] = typer.Option(
        None,
        "--package-json-file",
        "-j",
        help="Existing package.json file path(s) (default: package.json)",
        **existing_file_arg_config,
    ),
    no_sync_julia: Optional[bool] = typer.Option(
        None,
        "--no-sync-julia",
        "-L",
        help="Do not sync Project.toml (Julia) file (default: False)",
    ),
    julia_file: Optional[List[Path]] = typer.Option(
        None,
        "--julia-file",
        "-l",
        help="Custom Project.toml (Julia) file path(s) (default: Project.toml)",
        **existing_file_arg_config,
    ),
    no_sync_fortran: Optional[bool] = typer.Option(
        None,
        "--no-sync-fortran",
        "-F",
        help="Do not sync fpm.toml (Fortran) file (default: False)",
    ),
    fortran_file: Optional[List[Path]] = typer.Option(
        None,
        "--fortran-file",
        "-f",
        help="Custom fpm.toml (Fortran) file path(s) (default: fpm.toml)",
        **existing_file_arg_config,
    ),
    no_sync_pom_xml: Optional[bool] = typer.Option(
        None,
        "--no-sync-pomxml",
        "-X",
        help="Do not sync pom.xml (Java Maven) file (default: False)",
    ),
    pom_xml_file: Optional[List[Path]] = typer.Option(
        None,
        "--pomxml-file",
        "-x",
        help="Custom pom.xml (Java Maven) file path(s) (default: pom.xml)",
        **existing_file_arg_config,
    ),
    no_sync_mkdocs: Optional[bool] = typer.Option(
        None,
        "--no-sync-mkdocs",
        "-D",
        help="Do not sync mkdocs.yml file (default: False)",
    ),
    mkdocs_file: Optional[List[Path]] = typer.Option(
        None,
        "--mkdocs-file",
        "-d",
        help="Custom mkdocs.yml file path(s) (default: mkdocs.yml)",
        **existing_file_arg_config,
    ),
    no_sync_rust: Optional[bool] = typer.Option(
        None,
        "--no-sync-rust",
        "-R",
        help="Do not sync Cargo.toml file (default: False)",
    ),
    rust_file: Optional[List[Path]] = typer.Option(
        None,
        "--rust-file",
        "-r",
        help="Custom Cargo.toml file path(s) (default: Cargo.toml)",
        **existing_file_arg_config,
    ),
    no_sync_cff: Optional[bool] = typer.Option(
        None,
        "--no-sync-cff",
        "-C",
        help="Do not sync CITATION.cff file (default: False)",
    ),
    cff_file: Optional[List[Path]] = typer.Option(
        None,
        "--cff-file",
        "-c",
        help="CITATION.cff file path(s) (default: CITATION.cff)",
        **file_arg_config,
    ),
    no_sync_codemeta: Optional[bool] = typer.Option(
        None,
        "--no-sync-codemeta",
        "-M",
        help="Do not sync codemeta.json file (default: False)",
    ),
    codemeta_file: Optional[List[Path]] = typer.Option(
        None,
        "--codemeta-file",
        "-m",
        help="Custom codemeta.json file path(s) (default: codemeta.json)",
        **file_arg_config,
    ),
    merge_codemeta: Optional[bool] = typer.Option(
        False,
        "--merge/--overwrite",
        help="Merge codemeta.json with with an existing codemeta.json file (default: False)",
    ),
    pass_validation: Optional[bool] = typer.Option(
        False,
        "--pass-validation",
        "-P",
        help="Pass validation of metadata files (default: False)",
    ),
    packages: Optional[List[Path]] = typer.Option(
        None,
        "--packages",
        "-k",
        help="Packages (subfolders) for monorepos with their own somesy config.",
        **existing_file_arg_config,
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
    if not conf.no_sync_pyproject:
        logger.info(
            f"  - [italic]pyproject.toml[/italic]:\t[grey]{conf.pyproject_file}[/grey]"
        )
    if not conf.no_sync_package_json:
        logger.info(
            f"  - [italic]package.json[/italic]:\t[grey]{conf.package_json_file}[/grey]"
        )
    if not conf.no_sync_julia:
        logger.info(
            f"  - [italic]Project.toml[/italic]:\t[grey]{conf.julia_file}[/grey]\n"
        )
    if not conf.no_sync_fortran:
        logger.info(
            f"  - [italic]fpm.toml(fortran)[/italic]:\t[grey]{conf.fortran_file}[/grey]"
        )
    if not conf.no_sync_pom_xml:
        logger.info(
            f"  - [italic]pom.xml[/italic]:\t[grey]{conf.pom_xml_file}[/grey]\n"
        )
    if not conf.no_sync_mkdocs:
        logger.info(
            f"  - [italic]mkdocs.yml[/italic]:\t[grey]{conf.mkdocs_file}[/grey]"
        )
    if not conf.no_sync_rust:
        logger.info(f"  - [italic]Cargo.toml[/italic]:\t[grey]{conf.rust_file}[/grey]")

    if not conf.no_sync_cff:
        logger.info(f"  - [italic]CITATION.cff[/italic]:\t[grey]{conf.cff_file}[/grey]")
    if not conf.no_sync_codemeta:
        logger.info(
            f"  - [italic]codemeta.json[/italic]:\t[grey]{conf.codemeta_file}[/grey]\n"
        )
    # ----
    if conf.pass_validation:
        logger.info("[bold yellow]Passing validation of metadata files.[/bold yellow]")
    sync_command(somesy_input)
    # ----
    logger.info("[bold green]Metadata synchronization completed.[/bold green]")
