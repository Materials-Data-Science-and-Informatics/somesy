import pytest
from tomlkit import dump

from somesy.julia import Julia


def test_julia_validate_accept(load_files, file_types):
    """Validate by loading the data Project.toml file using the fixture."""
    load_files([file_types.JULIA])


def test_julia_validate(tmp_path):
    """Test validating a Project.toml file."""

    # create a Project.toml file but with a invalid values
    reject_julia_object = {
        "name": "somesy",
        "version": "abc",
        "authors": ["John Doe <"],
    }

    invalid_julia_path = tmp_path / "Project.toml"
    with open(invalid_julia_path, "w+") as f:
        dump(reject_julia_object, f)

    with pytest.raises(ValueError):
        Julia(invalid_julia_path)
