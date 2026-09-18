from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from somesy.cff import CFF
from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.core.models import Entity, Person, SomesyInput
from somesy.fortran import Fortran
from somesy.julia import Julia
from somesy.mkdocs import MkDocs
from somesy.package_json.writer import PackageJSON
from somesy.pom_xml.writer import POM
from somesy.pyproject import Pyproject
from somesy.rust import Rust

TEST_DIR = Path(__file__).resolve().parent

TEST_DATA_DIR = TEST_DIR / "data"
"""Location of the test input data."""


class FileTypes(Enum):
    POETRY = "poetry"
    POETRY2 = "poetry2"
    SETUPTOOLS = "setuptools"
    UV = "uv"
    CITATION = "citation"
    SOMESY = "somesy"
    PACKAGE_JSON = "package_json"
    JULIA = "julia"
    FORTRAN = "fortran"
    POM_XML = "pom_xml"
    MKDOCS = "mkdocs"
    RUST = "rust"


FILE_NAMES: dict[FileTypes, str] = {
    FileTypes.POETRY: "pyproject.toml",
    FileTypes.POETRY2: "pyproject2.toml",
    FileTypes.SETUPTOOLS: "pyproject.setuptools.toml",
    FileTypes.UV: "pyproject.uv.toml",
    FileTypes.CITATION: "CITATION.cff",
    FileTypes.SOMESY: "somesy.toml",
    FileTypes.PACKAGE_JSON: "package.json",
    FileTypes.JULIA: "Project.toml",
    FileTypes.FORTRAN: "fpm.toml",
    FileTypes.POM_XML: "pom.xml",
    FileTypes.MKDOCS: "mkdocs.yml",
    FileTypes.RUST: "Cargo.toml",
}
"""Name of the file in `tests/data` backing each file type."""

FILE_LOADERS: dict[FileTypes, Any] = {
    FileTypes.POETRY: Pyproject,
    FileTypes.POETRY2: Pyproject,
    FileTypes.SETUPTOOLS: Pyproject,
    FileTypes.UV: Pyproject,
    FileTypes.CITATION: CFF,
    FileTypes.SOMESY: SomesyInput.from_input_file,
    FileTypes.PACKAGE_JSON: PackageJSON,
    FileTypes.JULIA: Julia,
    FileTypes.FORTRAN: Fortran,
    FileTypes.POM_XML: POM,
    FileTypes.MKDOCS: MkDocs,
    FileTypes.RUST: Rust,
}
"""Callable turning the file of each file type into its somesy representation."""


@pytest.fixture(scope="session", autouse=True)
def init_somesy_logger():
    set_log_level(SomesyLogLevel.DEBUG)


@pytest.fixture
def somesy_input() -> SomesyInput:
    """Return a somesy input instance."""
    return SomesyInput.from_input_file(Path("tests/data/somesy.toml"))


@pytest.fixture
def file_types() -> type[FileTypes]:
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

    def _create_files(files: set[tuple[FileTypes, str]]):
        for file_tuple in files:
            file_type, file_name = file_tuple
            if not isinstance(file_type, FileTypes):
                raise ValueError(f"Invalid file type: {file_type}")
            write_file_name = tmp_path / Path(file_name)
            # create the subfolder (if file name is a path with folders)
            write_file_name.parent.mkdir(parents=True, exist_ok=True)

            read_file_name = TEST_DATA_DIR / FILE_NAMES[file_type]

            with open(read_file_name, "r") as f:
                content = f.read()
            with open(write_file_name, "w+") as f:
                f.write(content)

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

    def _load_files(files: set[FileTypes]):
        file_instances: dict[FileTypes, Any] = {}
        for file_type in files:
            if not isinstance(file_type, FileTypes):
                raise ValueError(f"Invalid file type: {file_type}")

            read_file_name = TEST_DATA_DIR / FILE_NAMES[file_type]
            file_instances[file_type] = FILE_LOADERS[file_type](read_file_name)

        return file_instances

    yield _load_files


@pytest.fixture
def person() -> Person:
    """Return example person."""
    p = {
        "given-names": "Jane",
        "email": "j.doe@example.com",
        "family-names": "Doe",
        "orcid": "https://orcid.org/0123-4567-8910",
    }
    ret = Person.model_validate(p)
    ret.set_key_order(list(p.keys()))  # custom order!
    return ret


@pytest.fixture
def entity() -> Entity:
    """Return example entity."""
    e = {"name": "Entity", "email": "entity@example.com"}
    ret = Entity.model_validate(e)
    ret.set_key_order(list(e.keys()))
    return ret


@pytest.fixture
def xml_examples():
    """Return path for an xml example file in test directory, based on file name."""

    def _xml_loader(filename: str) -> Path:
        return TEST_DATA_DIR / filename

    yield _xml_loader
