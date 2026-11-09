"""Update scalar project metadata in a somesy.toml file."""

from pathlib import Path

import tomlkit
from pydantic import ValidationError

from somesy.core.core import atomic_write, get_input_content
from somesy.core.models import PartialProjectMetadata, SomesyInput

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
    if "project" not in content:
        raise ValueError(
            f"No [project] table found in {input_file}; add one before using 'set'."
        )
    try:
        # only the changed field must be valid, the file may be incomplete
        PartialProjectMetadata.model_validate({**content["project"], field: value})
    except ValidationError as error:
        first = error.errors()[0]
        if first["type"] in ("enum", "literal_error"):
            reason = f"{first['input']!r} is not an allowed value"
            if field == "license":
                reason = f"{first['input']!r} is not a known SPDX license identifier"
        else:
            reason = first["msg"]
            if len(reason) > 200:
                reason = reason[:197] + "..."
        raise ValueError(f"Invalid value for '{field}': {reason}") from None
    content["project"][field] = value
    atomic_write(input_file, tomlkit.dumps(content))
