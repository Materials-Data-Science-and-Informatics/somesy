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
    sources: list[tuple[Path, dict[str, Any]]],
    git_metadata,
    non_interactive: bool = False,
) -> dict[str, Any]:
    """Prompt or warn for required metadata that harvesting did not provide."""
    harvested = [content for _, content in sources]
    if git_metadata is not None:
        harvested.append(
            git_metadata.model_dump(exclude_none=True, exclude_defaults=False)
        )
    fallback: dict[str, Any] = {}

    for field, prompt in {
        "name": "Project name",
        "description": "Project description",
    }.items():
        if not any(source.get(field) for source in harvested):
            if non_interactive:
                logger.warning("Missing required metadata: %s", field)
            else:
                fallback[field] = typer.prompt(prompt)

    if not any(source.get("license") for source in harvested):
        if non_interactive:
            logger.warning("Missing required metadata: license")
        else:
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
        if non_interactive:
            logger.warning("Missing required metadata: author")
        else:
            author_type = typer.prompt(
                "Author type", type=str, default="person"
            ).lower()
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
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Do not prompt for missing metadata; report warnings instead.",
    ),
):
    """Harvest project metadata and create a somesy.toml file."""
    if ctx.invoked_subcommand is not None:
        return
    root = Path.cwd()
    output = output_file if output_file.is_absolute() else root / output_file
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output}")
    sources = harvest_sources(root)
    git_metadata = harvest_git(root)
    fallback = _prompt_missing_metadata(sources, git_metadata, non_interactive)
    source_content = [content for _, content in sources]
    if fallback:
        source_content.append(fallback)
    metadata = merge_metadata(
        source_content, git_metadata, allow_incomplete=non_interactive
    )
    source_names = {path.name for path, _ in sources}
    incomplete = (
        any(
            getattr(metadata, field, None) is None
            for field in ("name", "description", "license")
        )
        or not metadata.authors()
    )
    config = None
    if source_names or incomplete:
        config_data = {
            f"no_sync_{key}": filename not in source_names
            for key, filename in {
                "pyproject": "pyproject.toml",
                "package_json": "package.json",
                "julia": "Project.toml",
                "fortran": "fpm.toml",
                "pom_xml": "pom.xml",
                "mkdocs": "mkdocs.yml",
                "rust": "Cargo.toml",
            }.items()
        }
        config = SomesyConfig.model_validate(config_data)
    write_somesy_file(metadata, output, config=config, overwrite=overwrite)
    typer.echo(f"Created {output}")


# (config key, prompt label, default file, sync by default)
_CONFIG_TARGETS = [
    ("cff", "CFF", "CITATION.cff", True),
    ("codemeta", "codemeta.json", "codemeta.json", True),
    ("pyproject", "pyproject.toml", "pyproject.toml", True),
    ("package_json", "package.json", "package.json", False),
    ("julia", "Project.toml (Julia)", "Project.toml", True),
    ("fortran", "fpm.toml (Fortran)", "fpm.toml", True),
    ("pom_xml", "pom.xml", "pom.xml", True),
    ("mkdocs", "mkdocs.yml", "mkdocs.yml", True),
    ("rust", "Cargo.toml", "Cargo.toml", True),
]


@app.command()
@wrap_exceptions
def config():
    """Set CLI configs for somesy."""
    # check if input file exists, if not, try to find it from default list
    input_file_default = discover_input()

    # prompt for inputs
    input_file = Path(typer.prompt("Input file path", default=input_file_default))
    options: dict[str, Any] = {"input_file": Path(input_file)}

    for key, label, default_file, default_sync in _CONFIG_TARGETS:
        options[f"no_sync_{key}"] = not typer.confirm(
            f"Do you want to sync to a {label} file?", default=default_sync
        )
        if target_file := typer.prompt(f"{label} file path", default=default_file):
            options[f"{key}_file"] = target_file

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
