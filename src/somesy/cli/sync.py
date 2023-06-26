"""Sync command for somesy."""
import logging
import traceback
from pathlib import Path
from typing import Optional

import typer
from rich.pretty import pretty_repr

from somesy.commands import sync as sync_command
from somesy.core.core import get_somesy_cli_config
from somesy.core.discover import discover_input
from somesy.core.log import SomesyLogLevel, get_log_level, set_log_level
from somesy.core.models import SomesyConfig

logger = logging.getLogger("somesy")

app = typer.Typer()


@app.callback(invoke_without_command=True)
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
    try:
        # ---------------
        # config assembly

        # cli_log_level is None if the user did not pass a log level (-> "default")
        cli_log_level: Optional[SomesyLogLevel] = get_log_level()

        # config from CLI (merged with possibly set CLI flags for logging)
        curr_log_level: SomesyLogLevel = cli_log_level or SomesyLogLevel.SILENT
        passed_cli_args = {
            k: v
            for k, v in dict(
                no_sync_cff=no_sync_cff,
                cff_file=cff_file,
                no_sync_pyproject=no_sync_pyproject,
                pyproject_file=pyproject_file,
                no_sync_codemeta=no_sync_codemeta,
                codemeta_file=codemeta_file,
                show_info=curr_log_level == SomesyLogLevel.INFO,
                verbose=curr_log_level == SomesyLogLevel.VERBOSE,
                debug=curr_log_level == SomesyLogLevel.DEBUG,
            ).items()
            if v is not None
        }
        cli_conf = SomesyConfig(**passed_cli_args)
        cli_conf = cli_conf.dict(exclude_none=True, exclude_defaults=True)
        logger.debug(f"CLI config (excluding defaults):\n{pretty_repr(cli_conf)}")

        # ----
        # now try to get config from a config file
        # check if input file exists, if not, try to find it from default list
        somesy_conf_file: Path = discover_input(input_file)
        file_conf = get_somesy_cli_config(somesy_conf_file)

        # convert logging flags into somesy log level (for comparison)
        config_log_level = SomesyLogLevel.from_flags(
            info=file_conf.show_info, verbose=file_conf.verbose, debug=file_conf.debug
        )
        # convert into dict
        file_conf = file_conf.dict(exclude_none=True, exclude_defaults=True)
        logger.debug(f"File config (excluding defaults):\n{pretty_repr(file_conf)}")

        # prioritized combination of config settings (cli overrides config file)
        conf = SomesyConfig(**{**file_conf, **cli_conf})

        # if the log level was not initialized using a common CLI flag yet,
        # set it according to the loaded configuration
        if cli_log_level is None:
            set_log_level(config_log_level)

        logger.debug(f"Combined config (Defaults + File + CLI):\n{pretty_repr(conf)}")
        # --------
        run_sync(conf)

    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)


def run_sync(conf: SomesyConfig):
    """Write log messages and run synchronization based on passed config."""
    logger.info("[bold green]Synchronizing project metadata...[/bold green]")
    logger.info("Files to sync:")
    if not conf.no_sync_pyproject:
        logger.info(
            f"  - [italic]pyproject.toml[/italic]:\t[grey]{conf.pyproject_file}[/grey]"
        )
    if not conf.no_sync_cff:
        logger.info(f"  - [italic]CITATION.cff[/italic]:\t[grey]{conf.cff_file}[/grey]")
    if not conf.no_sync_codemeta:
        logger.info(
            f"  - [italic]codemeta.json[/italic]:\t[grey]{conf.codemeta_file}[/grey]\n"
        )
    # ----
    sync_command(conf)
    # ----
    logger.info("[bold green]Metadata synchronization completed.[/bold green]")
