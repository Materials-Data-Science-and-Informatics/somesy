"""Set config files for somesy."""
import logging
from pathlib import Path

import typer

from somesy.commands import init_config
from somesy.core.core import discover_input
from somesy.core.log import SomesyLogLevel, set_log_level

from .util import wrap_exceptions

logger = logging.getLogger("somesy")
app = typer.Typer()


@app.command()
@wrap_exceptions
def config():
    """Set CLI configs for somesy."""
    # check if input file exists, if not, try to find it from default list
    input_file_default = discover_input()

    # prompt for inputs
    input_file = typer.prompt("Input file path", default=input_file_default)
    input_file = Path(input_file)
    options = {
        "input_file": input_file,
        "no_sync_cff": not typer.confirm(
            "Do you want to sync to a CFF file?", default=True
        ),
    }
    cff_file = typer.prompt("CFF file path", default="CITATION.cff")
    if cff_file is not None or cff_file != "":
        options["cff_file"] = cff_file

    options["no_sync_pyproject"] = not typer.confirm(
        "Do you want to sync to a pyproject.toml file?", default=True
    )

    pyproject_file = typer.prompt("pyproject.toml file path", default="pyproject.toml")
    if pyproject_file is not None or pyproject_file != "":
        options["pyproject_file"] = pyproject_file

    options["sync_package_json"] = typer.confirm(
        "Do you want to sync to a package.json file?", default=False
    )
    package_json_file = typer.prompt("package.json file path", default="package.json")
    if package_json_file is not None or package_json_file != "":
        options["package_json_file"] = package_json_file

    options["no_sync_codemeta"] = not typer.confirm(
        "Do you want to sync to a codemeta.json file?", default=True
    )
    codemeta_file = typer.prompt("codemeta.json file path", default="codemeta.json")
    if codemeta_file is not None or codemeta_file != "":
        options["codemeta_file"] = codemeta_file

    options["show_info"] = typer.confirm(
        "Do you want to show info about the sync process?"
    )
    options["verbose"] = typer.confirm("Do you want to show verbose logs?")
    options["debug"] = typer.confirm("Do you want to show debug logs?")

    set_log_level(
        SomesyLogLevel.from_flags(
            debug=options["debug"],
            verbose=options["verbose"],
            info=options["show_info"],
        )
    )

    logger.debug(f"CLI options entered: {options}")

    init_config(input_file, options)
    logger.info(
        f"[bold green]Input file is updated/created at {input_file}[/bold green]"
    )
