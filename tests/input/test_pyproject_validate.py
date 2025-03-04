import pytest
from tomlkit import dump

from somesy.pyproject import Pyproject


def test_poetry_validate_accept(load_files, file_types):
    """Validate by loading the data pyproject file using the fixture."""
    load_files([file_types.SETUPTOOLS])
    load_files([file_types.POETRY])  # Poetry v1
    load_files([file_types.POETRY2])  # Poetry v2


def test_poetry_validate(tmp_path):
    """Test validating a pyproject file in both poetry and setuptools formats."""

    # Test Poetry v1 format with invalid values
    reject_poetry_v1_object = {
        "tool": {
            "poetry": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]}
        }
    }
    invalid_poetry_path = tmp_path / "pyproject.toml"
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_poetry_v1_object, f)

    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # Test Poetry v2 format with invalid values
    reject_poetry_v2_object = {
        "tool": {"poetry": {}},
        "project": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]},
    }
    invalid_poetry_path = tmp_path / "pyproject2.toml"
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_poetry_v2_object, f)

    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # if we pass validation, it should not raise an error for either version
    Pyproject(invalid_poetry_path, pass_validation=True)

    # Test setuptools format with invalid values
    reject_setuptools_object = {
        "project": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]}
    }
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_setuptools_object, f)
    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # if we pass validation, it should not raise an error
    Pyproject(invalid_poetry_path, pass_validation=True)
