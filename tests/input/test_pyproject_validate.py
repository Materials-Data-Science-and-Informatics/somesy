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


def test_dynamic_version_setuptools_valid(tmp_path):
    """Setuptools: dynamic = ['version'] without version field should pass validation."""
    obj = {
        "project": {
            "name": "somesy",
            "description": "A test package",
            "dynamic": ["version"],
        }
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    p = Pyproject(path)
    assert "version" in p._dynamic_fields


def test_dynamic_version_poetry2_valid(tmp_path):
    """Poetry v2: dynamic = ['version'] without version field should pass validation."""
    obj = {
        "tool": {"poetry": {}},
        "project": {
            "name": "somesy",
            "description": "A test package",
            "dynamic": ["version"],
            "license": "MIT",
            "authors": [{"name": "John Doe", "email": "john@example.com"}],
        },
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    p = Pyproject(path)
    assert "version" in p._dynamic_fields


def test_missing_version_not_dynamic_setuptools_fails(tmp_path):
    """Setuptools: missing version without dynamic should fail validation."""
    obj = {
        "project": {
            "name": "somesy",
            "description": "A test package",
        }
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    with pytest.raises(ValueError, match="version"):
        Pyproject(path)


def test_missing_version_not_dynamic_poetry2_fails(tmp_path):
    """Poetry v2: missing version without dynamic should fail validation."""
    obj = {
        "tool": {"poetry": {}},
        "project": {
            "name": "somesy",
            "description": "A test package",
            "license": "MIT",
            "authors": [{"name": "John Doe", "email": "john@example.com"}],
        },
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    with pytest.raises(ValueError, match="version"):
        Pyproject(path)
