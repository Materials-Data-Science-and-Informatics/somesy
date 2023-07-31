"""Sync command for somesy."""
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.pretty import pretty_repr

from somesy.commands import sync as sync_command
from somesy.core.core import discover_input
from somesy.core.log import SomesyLogLevel, get_log_level, set_log_level
from somesy.core.models import SomesyConfig, SomesyInput

from .util import wrap_exceptions

logger = logging.getLogger("somesy")

app = typer.Typer()


@app.callback(invoke_without_command=True)
@wrap_exceptions
def sync(
    input_file: Path = typer.Option(
        None,
        "--input-file",
        "-i",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Somesy input file path (default: .somesy.toml)",
    ),
    no_sync_cff: bool = typer.Option(
        None,
        "--no-sync-cff",
        "-C",
        help="Do not sync CITATION.cff file (default: False)",
    ),
    cff_file: Path = typer.Option(
        None,
        "--cff-file",
        "-c",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="CITATION.cff file path (default: CITATION.cff)",
    ),
    no_sync_pyproject: bool = typer.Option(
        None,
        "--no-sync-pyproject",
        "-P",
        help="Do not sync pyproject.toml file (default: False)",
    ),
    pyproject_file: Path = typer.Option(
        None,
        "--pyproject-file",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Existing pyproject.toml file path (default: pyproject.toml)",
    ),
    no_sync_package_json: bool = typer.Option(
        None,
        "--no-sync-package-json",
        "-J",
        help="Do not sync package.json file (default: True)",
    ),
    package_json_file: Path = typer.Option(
        None,
        "--package-json-file",
        "-j",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Existing package.json file path (default: package.json)",
    ),
    no_sync_codemeta: bool = typer.Option(
        None,
        "--no-sync-codemeta",
        "-M",
        help="Do not sync codemeta.json file",
    ),
    codemeta_file: Path = typer.Option(
        None,
        "--codemeta-file",
        "-m",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Custom codemeta.json file path",
    ),
):
    """Sync project metadata input with metadata files."""
    # ---------------
    # config from CLI (merged with possibly set CLI flags for logging)
    passed_cli_args = {
        k: v
        for k, v in dict(
            input_file=discover_input(input_file),
            no_sync_cff=no_sync_cff,
            cff_file=cff_file,
            no_sync_pyproject=no_sync_pyproject,
            pyproject_file=pyproject_file,
            no_sync_package_json=no_sync_package_json,
            package_json_file=package_json_file,
            no_sync_codemeta=no_sync_codemeta,
            codemeta_file=codemeta_file,
        ).items()
        if v is not None
    }
    somesy_conf = SomesyConfig(**passed_cli_args)

    # cli_log_level is None if the user did not pass a log level (-> "default")
    cli_log_level: Optional[SomesyLogLevel] = get_log_level()

    if cli_log_level is not None:
        # update log level flags if cli log level was set
        somesy_conf.update_log_level(cli_log_level)

    somesy_input: SomesyInput = somesy_conf.get_input()

    if cli_log_level is None:
        # no cli log level -> set it according to the loaded configuration
        set_log_level(somesy_input.config.log_level())

    logger.debug(
        f"Combined config (Defaults + File + CLI):\n{pretty_repr(somesy_input.config)}"
    )
    # --------
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
    if not conf.no_sync_cff:
        logger.info(f"  - [italic]CITATION.cff[/italic]:\t[grey]{conf.cff_file}[/grey]")
    if not conf.no_sync_codemeta:
        logger.info(
            f"  - [italic]codemeta.json[/italic]:\t[grey]{conf.codemeta_file}[/grey]\n"
        )
    # ----
    sync_command(somesy_input)
    # ----
    logger.info("[bold green]Metadata synchronization completed.[/bold green]")
