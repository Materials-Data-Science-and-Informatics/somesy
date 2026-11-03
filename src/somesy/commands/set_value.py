"""Update scalar project metadata in a somesy.toml file."""

from pathlib import Path

import tomlkit
from pydantic import ValidationError

from somesy.core.core import get_input_content
from somesy.core.models import ProjectMetadata, SomesyInput

SETTABLE_FIELDS = {
    "name",
    "description",
    "abstract",
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
    try:
        ProjectMetadata.model_validate({**content["project"], field: value})
    except ValidationError as error:
        first = error.errors()[0]
        raise ValueError(f"Invalid value for '{field}': {first['msg']}") from None
    content["project"][field] = value
    with open(input_file, "w", encoding="utf-8") as file:
        tomlkit.dump(content, file)
