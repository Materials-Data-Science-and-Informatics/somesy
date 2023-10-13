from enum import Enum
from pathlib import Path
from typing import Any, Dict, Set, Tuple, Type

import pytest

from somesy.cff import CFF
from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.core.models import Person, SomesyInput
from somesy.package_json.writer import PackageJSON
from somesy.pyproject import Pyproject


class FileTypes(Enum):
    POETRY = "poetry"
    SETUPTOOLS = "setuptools"
    CITATION = "citation"
    SOMESY = "somesy"
    PACKAGE_JSON = "package_json"


@pytest.fixture(scope="session", autouse=True)
def init_somesy_logger():
    set_log_level(SomesyLogLevel.DEBUG)


@pytest.fixture
def somesy_input() -> dict:
    """Return a somesy input instance."""
    return SomesyInput.from_input_file(Path("tests/data/somesy.toml"))


@pytest.fixture
def file_types() -> Type[FileTypes]:
    """Return a FileTypes instance."""
    return FileTypes


@pytest.fixture
def create_files(tmp_path):
    """Create file types with given file names with a dict input, return the folder location.

    Example:
    ```python
    files = [{FileTypes.POETRY: 'pyproject.poetry.toml'}, {FileTypes.SETUPTOOLS: 'pyproject.setuptools.toml'}, ...]
    # file_dir folder has the requested files
    file_dir = create_files(files)
    ```
    """

    def _create_files(files: Set[Tuple[FileTypes, str]]):
        for file_tuple in files:
            file_type, file_name = file_tuple
            if not isinstance(file_type, FileTypes):
                raise ValueError(f"Invalid file type: {file_type}")
            write_file_name = tmp_path / Path(file_name)

            read_file_path = Path("tests/data")
            read_file_name: Path = None
            # set file name as the input, if not given set to default
            if file_type == FileTypes.CITATION:
                read_file_name = read_file_path / Path("CITATION.cff")
            elif file_type == FileTypes.SETUPTOOLS:
                read_file_name = read_file_path / Path("pyproject.setuptools.toml")
            elif file_type == FileTypes.POETRY:
                read_file_name = read_file_path / Path("pyproject.toml")
            elif file_type == FileTypes.SOMESY:
                read_file_name = read_file_path / Path("somesy.toml")
            elif file_type == FileTypes.PACKAGE_JSON:
                read_file_name = read_file_path / Path("package.json")

            with open(read_file_name, "r") as f:
                content = f.read()
                with open(write_file_name, "w+") as f2:
                    f2.write(content)

        return tmp_path

    yield _create_files


@pytest.fixture
def load_files():
    """Read and load files to defined classes, return a dict with those class instances.

    Example:
    ```python
    files = [FileTypes.POETRY, FileTypes.SETUPTOOLS, ...]
    # file_instances dict has the instances of the requested files
    file_instances = load_files(files)
    ```
    """

    def _load_files(files: Set[FileTypes]):
        file_instances: Dict[FileTypes, Any] = {}
        for file_type in files:
            if not isinstance(file_type, FileTypes):
                raise ValueError(f"Invalid file type: {file_type}")

            read_file_name = Path("tests/data")
            if file_type == FileTypes.CITATION:
                read_file_name = read_file_name / Path("CITATION.cff")
                file_instances[file_type] = CFF(read_file_name)
            elif file_type == FileTypes.SETUPTOOLS:
                read_file_name = read_file_name / Path("pyproject.setuptools.toml")
                file_instances[file_type] = Pyproject(read_file_name)
            elif file_type == FileTypes.POETRY:
                read_file_name = read_file_name / Path("pyproject.toml")
                file_instances[file_type] = Pyproject(read_file_name)
            elif file_type == FileTypes.SOMESY:
                read_file_name = read_file_name / Path("somesy.toml")
                file_instances[file_type] = SomesyInput.from_input_file(read_file_name)
            elif file_type == FileTypes.PACKAGE_JSON:
                read_file_name = read_file_name / Path("package.json")
                file_instances[file_type] = PackageJSON(read_file_name)

        return file_instances

    yield _load_files


@pytest.fixture
def person() -> Person:
    p = {
        "given-names": "Jane",
        "email": "j.doe@example.com",
        "family-names": "Doe",
        "orcid": "https://orcid.org/0123-4567-8910",
    }
    ret = Person.model_validate(p)
    ret.set_key_order(list(p.keys()))  # custom order!
    return ret
