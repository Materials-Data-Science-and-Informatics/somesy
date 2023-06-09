from pathlib import Path

import pytest

from somesy.core.log import SomesyLogLevel, set_log_level


@pytest.fixture(scope="session", autouse=True)
def init_somesy_logger():
    set_log_level(SomesyLogLevel.DEBUG)


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


@pytest.fixture
def create_somesy_metadata():
    def _create_somesy_metadata(somesy_file: Path):
        # create somesy file beforehand
        with open("tests/core/data/.somesy.toml", "r") as f:
            content = f.read()
            with open(somesy_file, "w+") as f2:
                f2.write(content)

    yield _create_somesy_metadata


@pytest.fixture
def create_somesy_metadata_config():
    def _create_somesy_metadata_config(somesy_file: Path):
        # create somesy file beforehand
        with open("tests/core/data/.somesy.with_config.toml", "r") as f:
            content = f.read()
            with open(somesy_file, "w+") as f2:
                f2.write(content)

    yield _create_somesy_metadata_config
