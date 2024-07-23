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
    options = dict(input_file=Path(input_file))

    # ----

    options["no_sync_cff"] = not typer.confirm(
        "Do you want to sync to a CFF file?", default=True
    )
    if cff_file := typer.prompt("CFF file path", default="CITATION.cff"):
        options["cff_file"] = cff_file

    options["no_sync_codemeta"] = not typer.confirm(
        "Do you want to sync to a codemeta.json file?", default=True
    )
    if codemeta_file := typer.prompt(
        "codemeta.json file path", default="codemeta.json"
    ):
        options["codemeta_file"] = codemeta_file

    options["no_sync_pyproject"] = not typer.confirm(
        "Do you want to sync to a pyproject.toml file?", default=True
    )
    if pyproject_file := typer.prompt(
        "pyproject.toml file path", default="pyproject.toml"
    ):
        options["pyproject_file"] = pyproject_file

    options["sync_package_json"] = typer.confirm(
        "Do you want to sync to a package.json file?", default=False
    )
    if package_json_file := typer.prompt(
        "package.json file path", default="package.json"
    ):
        options["package_json_file"] = package_json_file

    options["no_sync_julia"] = not typer.confirm(
        "Do you want to sync to a Project.toml(Julia) file?", default=True
    )
    if julia_file := typer.prompt(
        "Project.toml (Julia) file path", default="Project.toml"
    ):
        options["julia_file"] = julia_file

    options["no_sync_fortran"] = not typer.confirm(
        "Do you want to sync to a fpm.toml(fortran) file?", default=True
    )
    fortran_file = typer.prompt("fpm.toml(fortran) file path", default="fpm.toml")
    if fortran_file is not None or fortran_file != "":
        options["fortran_file"] = fortran_file

    options["no_sync_pom_xml"] = not typer.confirm(
        "Do you want to sync to a pom.xml file?", default=True
    )
    if pom_xml_file := typer.prompt("pom.xml file path", default="pom.xml"):
        options["pom_xml_file"] = pom_xml_file

    options["no_sync_mkdocs"] = not typer.confirm(
        "Do you want to sync to a mkdocs.yml file?", default=True
    )
    if mkdocs_file := typer.prompt("mkdocs.yml file path", default="mkdocs.yml"):
        options["mkdocs_file"] = mkdocs_file

    options["no_sync_rust"] = not typer.confirm(
        "Do you want to sync to a Cargo.toml file?", default=True
    )
    if rust_file := typer.prompt("Cargo.toml file path", default="Cargo.toml"):
        options["rust_file"] = rust_file

    # ----

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
