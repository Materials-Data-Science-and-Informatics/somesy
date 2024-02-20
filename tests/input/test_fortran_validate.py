import pytest
from tomlkit import dump

from somesy.fortran import Fortran


def test_fortran_validate_accept(load_files, file_types):
    """Validate by loading the data fpm.toml file using the fixture."""
    load_files([file_types.FORTRAN])


def test_fortran_validate(tmp_path):
    """Test validating a fpm.toml file."""

    # create a fpm.toml file but with a invalid values
    reject_fortran_object = {
        "name": "12somesy",
        "version": "abc",
        "authors": ["John Doe <"],
    }

    invalid_fortran_path = tmp_path / "fpm.toml"
    with open(invalid_fortran_path, "w+") as f:
        dump(reject_fortran_object, f)

    with pytest.raises(ValueError):
        Fortran(invalid_fortran_path)
