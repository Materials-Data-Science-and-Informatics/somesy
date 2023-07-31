import pytest
from pathlib import Path
from somesy.package_json.writer import PackageJSON


def test_load():
    not_exist_path = Path("reject/package.json")
    with pytest.raises(FileNotFoundError):
        PackageJSON(not_exist_path)

    file_path = Path("tests/package_json/data/package.json")
    PackageJSON(file_path)
    assert file_path.is_file()

    reject_path = Path("tests/package_json/data/reject/package.json")
    with pytest.raises(ValueError):
        PackageJSON(reject_path)


def test_sync(somesy, package_json):
    metadata = somesy.project
    package_json.sync(metadata)
    assert package_json.name == "testproject"
    assert package_json.version == "1.0.0"
    assert (
        package_json.description == "This is a test project for demonstration purposes."
    )
