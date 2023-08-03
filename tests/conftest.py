from pathlib import Path

import pytest

from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.core.models import SomesyInput
from somesy.package_json.writer import PackageJSON


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
def create_somesy():
    def _create_somesy(somesy_file: Path):
        # create somesy file beforehand
        with open("tests/data/somesy.toml", "r") as f:
            content = f.read()
            with open(somesy_file, "w+") as f2:
                f2.write(content)

    yield _create_somesy


@pytest.fixture
def create_package_json():
    def _create_package_json(package_json_file: Path):
        # create somesy file beforehand
        with open("tests/data/package.json", "r") as f:
            content = f.read()
            with open(package_json_file, "w+") as f2:
                f2.write(content)

    yield _create_package_json


@pytest.fixture
def create_cff_file():
    def _create_cff_file(cff_file: Path):
        # create somesy file beforehand
        with open("tests/cff/data/CITATION.cff", "r") as f:
            content = f.read()
            with open(cff_file, "w+") as f2:
                f2.write(content)

    yield _create_cff_file


@pytest.fixture
def somesy() -> dict:
    return SomesyInput.from_input_file(Path("tests/data/somesy.toml"))


@pytest.fixture
def package_json() -> dict:
    return PackageJSON(Path("tests/data/package.json"))
