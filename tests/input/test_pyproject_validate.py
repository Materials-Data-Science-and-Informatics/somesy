import pytest
from tomlkit import dump

from somesy.pyproject import Pyproject


def test_poetry_setuptools_validate_accept(load_files, file_types):
    """Validate by loading the data pyproject file using the fixture."""
    load_files([file_types.SETUPTOOLS])
    load_files([file_types.POETRY])


def test_poetry_dependencies_validate(load_files, file_types):
    files = load_files([file_types.POETRY])
    poetry = files[file_types.POETRY]

    # there are 3 dependencies in the poetry file
    assert len(poetry.dependencies) == 3

    # check version of the first dependency
    assert poetry.dependencies["python"] == "^3.8"


def test_poetry_validate(tmp_path):
    """Test validating a pyproject file in both poetry and setuptools formats."""

    # create a pyproject file in poetry format but with a invalid values
    reject_poetry_object = {
        "tool": {
            "poetry": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]}
        }
    }
    invalid_poetry_path = tmp_path / "pyproject.toml"
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_poetry_object, f)

    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # create a pyproject file in setuptools format but with a invalid values
    reject_setuptools_object = {
        "project": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]}
    }
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_setuptools_object, f)
    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)
