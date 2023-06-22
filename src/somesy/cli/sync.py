"""Sync command for somesy."""
import logging
import traceback
from pathlib import Path

import typer
from rich.pretty import pretty_repr

from somesy.commands import sync as sync_command
from somesy.core.core import get_somesy_cli_config
from somesy.core.discover import discover_input
from somesy.core.log import set_logger
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
    show_info: bool = typer.Option(
        None,
        "--show-info",
        "-s",
        help="Get basic output (somesy is quiet by default) (default: False)",
    ),
    verbose: bool = typer.Option(
        None,
        "--verbose",
        "-v",
        help="Verbose output (default: False)",
    ),
    debug: bool = typer.Option(
        None,
        "--debug",
        "-d",
        help="Debug output (default: False)",
    ),
):
    """Sync project metadata input with metadata files."""
    set_logger(debug=debug, verbose=verbose, info=show_info)

    try:
        # ---------------
        # config assembly

        # config from CLI
        passed_cli_args = {
            k: v
            for k, v in dict(
                no_sync_cff=no_sync_cff,
                cff_file=cff_file,
                no_sync_pyproject=no_sync_pyproject,
                pyproject_file=pyproject_file,
                no_sync_codemeta=no_sync_codemeta,
                codemeta_file=codemeta_file,
                show_info=show_info,
                verbose=verbose,
                debug=debug,
            ).items()
            if v is not None
        }
        cli_conf = SomesyConfig(**passed_cli_args)
        cli_conf = cli_conf.dict(exclude_none=True, exclude_defaults=True)
        logger.debug(f"CLI config (excluding defaults):\n{pretty_repr(cli_conf)}")

        # config from file
        # check if input file exists, if not, try to find it from default list
        somesy_conf_file: Path = discover_input(input_file)
        file_conf = get_somesy_cli_config(somesy_conf_file)
        file_conf = file_conf.dict(exclude_none=True, exclude_defaults=True)
        logger.debug(f"File config (excluding defaults):\n{pretty_repr(file_conf)}")

        # prioritized combination
        conf = SomesyConfig(**{**file_conf, **cli_conf})

        # --------

        set_logger(  # re-init logger (level could be overridden)
            debug=conf.debug,
            verbose=conf.verbose,
            info=conf.show_info,
        )
        logger.debug(f"Combined config (Defaults + File + CLI):\n{pretty_repr(conf)}")

        # info output
        logger.info("[bold green]Syncing project metadata...[/bold green]\n")
        logger.info("Files to sync:")
        if not conf.no_sync_pyproject:
            logger.info(
                f"  - [italic]pyproject.toml[/italic]\t[grey]{conf.pyproject_file}[/grey]"
            )
        if not conf.no_sync_cff:
            logger.info(
                f"  - [italic]CITATION.cff[/italic]:\t[grey]{conf.cff_file}[/grey]"
            )
        if not conf.no_sync_codemeta:
            logger.info(
                f"  - [italic]codemeta.json[/italic]:\t[grey]{conf.codemeta_file}[/grey]"
            )

        # ----------
        # sync files (passing paths only if the target is not disabled)
        sync_command(
            input_file=conf.input_file,
            pyproject_file=conf.pyproject_file if not conf.no_sync_pyproject else None,
            cff_file=conf.cff_file if not conf.no_sync_cff else None,
            codemeta_file=conf.codemeta_file if not conf.no_sync_codemeta else None,
        )

        logger.info("[bold green]Syncing completed.[/bold green]")

    except Exception as e:
        logger.error(f"[bold red]Error: {e}[/bold red]")
        logger.debug(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)
