"""Core somesy functions."""
from pathlib import Path

from tomlkit import load

from somesy.core.models import ProjectMetadata


def get_project_metadata(path: Path) -> ProjectMetadata:
    """Return project metadata to from different sources as a simple dict. Currently, only pyproject.toml inputs are supported.

    Args:
        path (Path): input source path

    Returns:
        ProjectMetadata: project metadata input to sync output files
    """
    # load the pyproject.toml file
    if path.suffix == ".toml":
        with open(path, "r") as f:
            input = load(f)

        # load project metadata
        if "somesy" in path.name and "project" in input:
            metadata = input["project"]
            try:
                metadata = metadata.unwrap()
                return ProjectMetadata(**metadata)
            except Exception as e:
                raise ValueError(f"Somesy input validation failed: {e}")

        elif (
            "pyproject" in path.name
            and "tool" in input
            and "somesy" in input["tool"]
            and "project" in input["tool"]["somesy"]
        ):
            metadata = input["tool"]["somesy"]["project"]
            try:
                metadata = metadata.unwrap()
                return ProjectMetadata(**metadata)
            except Exception as e:
                raise ValueError(f"Somesy input validation failed: {e}")
        else:
            raise ValueError("Somesy input not found.")
    else:
        raise ValueError("Only toml files are supported for reading somesy input.")
