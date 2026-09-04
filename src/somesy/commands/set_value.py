"""Update scalar project metadata in a somesy.toml file."""

from pathlib import Path

import tomlkit

from somesy.core.core import get_input_content
from somesy.core.models import ProjectMetadata, SomesyInput

SETTABLE_FIELDS = {
    "name",
    "description",
    "version",
    "license",
    "homepage",
    "repository",
    "documentation",
}


def set_project_value(input_file: Path, field: str, value: str) -> None:
    """Set one scalar project-metadata value in a somesy.toml file."""
    if field not in SETTABLE_FIELDS:
        allowed = ", ".join(sorted(SETTABLE_FIELDS))
        raise ValueError(f"Unknown project field '{field}'. Choose one of: {allowed}.")
    if not SomesyInput.is_somesy_file_path(input_file):
        raise ValueError("The input file must be a somesy.toml file.")

    content = get_input_content(input_file, no_unwrap=True)
    ProjectMetadata.model_validate({**content["project"], field: value})
    content["project"][field] = value
    with open(input_file, "w") as file:
        tomlkit.dump(content, file)
