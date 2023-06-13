from pathlib import Path

import pytest

from somesy.core.utils import set_logger


@pytest.fixture
def create_poetry_file():
    def _create_poetry_file(pyproject_file: Path):
        # create pyproject file beforehand
        with open("tests/pyproject/data/pyproject.full.toml", "r") as f:
            pyproject_content = f.read()
            with open(pyproject_file, "w+") as f2:
                f2.write(pyproject_content)

    yield _create_poetry_file


@pytest.fixture
def create_setuptools_file():
    def _create_setuptools_file(pyproject_file: Path):
        # create pyproject file beforehand
        with open("tests/pyproject/data/pyproject.setuptools.toml", "r") as f:
            pyproject_content = f.read()
            with open(pyproject_file, "w+") as f2:
                f2.write(pyproject_content)

    yield _create_setuptools_file


@pytest.fixture(scope="session", autouse=True)
def init_somesy_logger():
    set_logger(debug=True)
