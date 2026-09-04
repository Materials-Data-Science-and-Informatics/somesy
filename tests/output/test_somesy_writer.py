"""Tests for writing standalone Somesy metadata."""

import pytest

from somesy.commands.init_config import write_somesy_file
from somesy.core.core import get_input_content
from somesy.core.models import LicenseEnum, Person, ProjectMetadata, SomesyInput


def metadata():
    """Return representative project metadata."""
    return ProjectMetadata(
        name="example",
        description="An example project",
        license=LicenseEnum.MIT,
        people=[Person(given_names="Jane", family_names="Doe", author=True)],
        keywords=["metadata"],
    )


def test_write_somesy_file_round_trips(tmp_path):
    path = tmp_path / "somesy.toml"

    write_somesy_file(metadata(), path)

    loaded = SomesyInput(**get_input_content(path))
    assert loaded.project.name == "example"
    assert loaded.project.license == LicenseEnum.MIT
    assert loaded.project.people[0].full_name == "Jane Doe"


def test_write_somesy_file_refuses_to_overwrite(tmp_path):
    path = tmp_path / "somesy.toml"
    path.write_text("existing = true\n")

    with pytest.raises(FileExistsError):
        write_somesy_file(metadata(), path)

    write_somesy_file(metadata(), path, overwrite=True)
    assert "[project]" in path.read_text()
