from pydantic import ValidationError
import pytest
from tomlkit import dump

from somesy.rust import Rust


def test_rust_validate_accept(load_files, file_types):
    """Validate by loading the data Cargo.toml file using the fixture."""
    load_files([file_types.RUST])


def test_rust_validate(tmp_path):
    """Test validating a Cargo.toml file."""

    # create a Cargo.toml file but with a invalid version value
    reject_rust_object = {
        "package": {
            "name": "somesy",
            "version": "abc",
            "authors": ["John Doe <"],
        }
    }

    invalid_rust_path = tmp_path / "Cargo.toml"
    with open(invalid_rust_path, "w+") as f:
        dump(reject_rust_object, f)

    with pytest.raises(ValidationError):
        Rust(invalid_rust_path)

    # reject with invalid values
    _reject_with(tmp_path, "name", "1test-")
    _reject_with(tmp_path, "keywords", ["testtesttesttesttesttesttest"])
    _reject_with(tmp_path, "keywords", ["test test"])
    _reject_with(tmp_path, "keywords", ["test*test"])
    _reject_with(
        tmp_path, "keywords", ["test", "test2", "test3", "test4", "test5", "test6"]
    )
    _reject_with(tmp_path, "license_file", "LICENSE")


def _reject_with(tmp_path, key, value):
    """Helper function to reject invalid values."""
    reject_rust_object = {
        "package": {
            "name": "somesy",
            "version": "1.0.0",
            "license": "MIT",
        }
    }
    reject_rust_object["package"][key] = value
    invalid_rust_path = tmp_path / "Cargo.toml"
    with open(invalid_rust_path, "w+") as f:
        dump(reject_rust_object, f)

    with pytest.raises(ValueError):
        Rust(invalid_rust_path)
