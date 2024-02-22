import pytest
from ruamel.yaml import YAML

from somesy.mkdocs.writer import MkDocs


def test_mkdocs_validate_accept(load_files, file_types):
    """Validate by loading the data file using the fixture."""
    load_files([file_types.MKDOCS])


def test_mkdocs_validate_reject(tmp_path):
    """Test validating a mkdocs file."""
    mkdocs_path = tmp_path / "mkdocs.yml"

    # create a mkdocs file with a invalid version
    reject_mkdocs_object = {"site_description": "A project"}
    yaml = YAML()
    yaml.dump(reject_mkdocs_object, mkdocs_path)

    # try to load the mkdocs file
    with pytest.raises(ValueError):
        MkDocs(mkdocs_path)
