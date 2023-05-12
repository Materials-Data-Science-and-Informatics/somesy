"""Core somesy functions."""
from pathlib import Path

from tomlkit import load

from somesy.core.models import ProjectMetadata


def get_project_metadata(path: Path) -> ProjectMetadata:
    """Return project metadata to from different sources as a simple dict. Currently, only pyproject.toml inputs are supported.

    Args:
        path (Path): config source path

    Returns:
        ProjectMetadata: project metadata input to sync output files
    """
    # load the pyproject.toml file
    if path.suffix == ".toml":
        try:
            with open(path, "r") as f:
                config = load(f)
        except FileNotFoundError:
            raise FileNotFoundError("pyproject.toml not found")

        # load project metadata
        if (
            "tool" in config
            and "somesy" in config["tool"]
            and "project" in config["tool"]["somesy"]
        ):
            metadata = config["tool"]["somesy"]["project"]
            try:
                metadata = metadata.unwrap()
                return ProjectMetadata(**metadata)
            except Exception as e:
                raise ValueError(f"Somesy input validation failed: {e}")
        else:
            raise ValueError("Somesy config not found in pyproject.toml file.")
    else:
        raise ValueError("Only toml files are supported for reading project metadata.")
