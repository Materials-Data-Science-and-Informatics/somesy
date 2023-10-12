from json import dump

import pytest

from somesy.package_json import PackageJSON


def test_package_json_validate_accept(load_files, file_types):
    """Validate by loading the data package.json file using the fixture."""
    load_files([file_types.PACKAGE_JSON])


def test_package_json_validate(tmp_path):
    """Test validating a package.json file in both package_json and setuptools formats."""

    # create a package.json file in package.json format but with a invalid values
    reject_package_json_object = {
        "name": "somesy",
        "version": "abc",
        "authors": "John Doe",
    }
    invalid_package_json_path = tmp_path / "package.json"
    with open(invalid_package_json_path, "w+") as f:
        dump(reject_package_json_object, f)

    with pytest.raises(ValueError):
        PackageJSON(invalid_package_json_path)
