from typing import OrderedDict
from somesy.commands.sync import sync
from somesy.core.models import ProjectMetadata, SomesyConfig, SomesyInput, Person
from somesy.pyproject.writer import Pyproject
from somesy.package_json.writer import PackageJSON
from somesy.cff.writer import CFF


def test_sync(tmp_path, create_poetry_file, create_package_json, create_cff_file):
    # Create a temporary pyproject.toml file
    pyproject_file = tmp_path / "pyproject.toml"
    create_poetry_file(pyproject_file)
    pyproject = Pyproject(pyproject_file)

    # Create a temporary CITATION.cff file
    cff_file = tmp_path / "CITATION.cff"
    create_cff_file(cff_file)
    cff = CFF(cff_file)

    # Create a temporary package.json file
    package_json_file = tmp_path / "package.json"
    create_package_json(package_json_file)
    package_json = PackageJSON(package_json_file)

    # Create a SomesyInput object with some metadata
    metadata = ProjectMetadata(
        name="test-project",
        version="0.1.0",
        description="A test project",
        people=[
            Person(
                given_names="Alice", family_names="Joe", email="a@a.aa", author=True
            ),
            Person(given_names="Bob", family_names="Joe", email="b@b.bb"),
        ],
        license="MIT",
    )
    conf = SomesyConfig(
        pyproject_file=pyproject_file,
        cff_file=cff_file,
        sync_package_json=True,
        package_json_file=package_json_file,
        no_sync_codemeta=True,
    )
    somesy_input = SomesyInput(config=conf, project=metadata)

    # Call the sync function
    sync(
        somesy_input,
    )

    # Check that the pyproject.toml file was synced
    pyproject = Pyproject(pyproject_file)
    assert pyproject.name == "test-project"
    assert pyproject.version == "0.1.0"
    assert pyproject.description == "A test project"
    assert pyproject.authors == ["Alice Joe <a@a.aa>"]
    assert pyproject.license == "MIT"

    # Check that the CITATION.cff file was synced
    cff = CFF(cff_file)
    assert cff.name == "test-project"
    assert cff.version == "0.1.0"
    assert cff.description == "A test project"
    assert cff.authors == [
        {"given-names": "Alice", "email": "a@a.aa", "family-names": "Joe"}
    ]
    assert cff.license == "MIT"

    # Check that the package.json file was synced
    package_json = PackageJSON(package_json_file)
    assert package_json.name == "test-project"
    assert package_json.version == "0.1.0"
    assert package_json.description == "A test project"
    assert package_json.authors == [
        OrderedDict([("name", "Alice Joe"), ("email", "a@a.aa")])
    ]
    assert package_json.license == "MIT"
