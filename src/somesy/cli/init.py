"""Set config files for somesy."""

import logging
from pathlib import Path
from typing import Any

import typer

from somesy.commands import init_config, write_somesy_file
from somesy.core.core import discover_input
from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.core.models import Person, SomesyConfig
from somesy.core.types import LicenseEnum
from somesy.git.harvest import harvest as harvest_git
from somesy.harvest import harvest_sources
from somesy.merge import merge_metadata

from .util import file_arg_config, wrap_exceptions

logger = logging.getLogger("somesy")
app = typer.Typer()


def _prompt_missing_metadata(
    sources: list[tuple[Path, dict[str, Any]]], git_metadata
) -> dict[str, Any]:
    """Prompt for required metadata that harvesting did not provide."""
    harvested = [content for _, content in sources]
    if git_metadata is not None:
        harvested.append(git_metadata.model_dump(exclude_none=True))
    fallback: dict[str, Any] = {}

    for field, prompt in {
        "name": "Project name",
        "description": "Project description",
    }.items():
        if not any(source.get(field) for source in harvested):
            fallback[field] = typer.prompt(prompt)

    if not any(source.get("license") for source in harvested):
        while True:
            value = typer.prompt("SPDX license")
            try:
                fallback["license"] = LicenseEnum(value)
                break
            except ValueError:
                typer.echo(f"Unknown SPDX license: {value}")

    def is_author(person: Any) -> bool:
        return (
            person.get("author", False)
            if isinstance(person, dict)
            else getattr(person, "author", False)
        )

    has_author = any(
        any(is_author(person) for person in source.get(key, []) or [])
        for source in harvested
        for key in ("people", "entities", "authors")
    )
    if not has_author:
        author_type = typer.prompt("Author type", type=str, default="person").lower()
        while author_type not in {"person", "entity"}:
            typer.echo("Author type must be 'person' or 'entity'.")
            author_type = typer.prompt("Author type", default="person").lower()
        if author_type == "person":
            person = {
                "given_names": typer.prompt("Author given names"),
                "family_names": typer.prompt("Author family names"),
                "author": True,
            }
            email = typer.prompt("Author email", default="")
            if email:
                person["email"] = email
            fallback["people"] = [Person(**person)]
        else:
            name = typer.prompt("Author organization")
            fallback["entities"] = [{"name": name, "author": True}]
            email = typer.prompt("Author email", default="")
            if email:
                fallback["entities"][0]["email"] = email

    return fallback


@app.callback(invoke_without_command=True)
@wrap_exceptions
def initialize(
    ctx: typer.Context,
    output_file: Path = typer.Option(
        Path("somesy.toml"),
        "--output-file",
        "-o",
        help="Path for the generated somesy.toml file (default: somesy.toml).",
        **file_arg_config,
    ),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Harvest project metadata and create a somesy.toml file."""
    if ctx.invoked_subcommand is not None:
        return
    root = Path.cwd()
    sources = harvest_sources(root)
    git_metadata = harvest_git(root)
    fallback = _prompt_missing_metadata(sources, git_metadata)
    source_content = [content for _, content in sources]
    if fallback:
        source_content.append(fallback)
    metadata = merge_metadata(source_content, git_metadata)
    source_names = {path.name for path, _ in sources}
    config = None
    if source_names:
        config = SomesyConfig(
            **{
                f"no_sync_{key}": filename not in source_names
                for key, filename in {
                    "pyproject": "pyproject.toml",
                    "package_json": "package.json",
                    "julia": "Project.toml",
                    "fortran": "fpm.toml",
                    "pom_xml": "pom.xml",
                    "mkdocs": "mkdocs.yml",
                    "rust": "Cargo.toml",
                    "cff": "CITATION.cff",
                    "codemeta": "codemeta.json",
                }.items()
            }
        )
    output = output_file if output_file.is_absolute() else root / output_file
    write_somesy_file(metadata, output, config=config, overwrite=overwrite)
    typer.echo(f"Created {output}")


@app.command()
@wrap_exceptions
def config():
    """Set CLI configs for somesy."""
    # check if input file exists, if not, try to find it from default list
    input_file_default = discover_input()

    # prompt for inputs
    input_file = Path(typer.prompt("Input file path", default=input_file_default))
    options: dict[str, Any] = {"input_file": Path(input_file)}

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
