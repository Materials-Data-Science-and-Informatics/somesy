from pathlib import Path

import pytest

from somesy.core.core import get_project_metadata
from somesy.core.utils import set_logger
from somesy.pyproject.core import Pyproject


@pytest.fixture(autouse=True)
def set_log_level():
    set_logger(debug=False, verbose=False)


@pytest.fixture
def path():
    return Path("tests/pyproject/data/pyproject.full.toml")


@pytest.fixture
def pyproject(path):
    return Pyproject(path)


@pytest.fixture
def project_metadata(path):
    return get_project_metadata(path)


def test_pyproject_init(pyproject, path):
    assert pyproject.path == path


def test_sync(pyproject, project_metadata):
    pyproject.sync(project_metadata)

    assert pyproject.version == "0.1.0"
