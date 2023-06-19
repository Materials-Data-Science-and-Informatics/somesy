from pathlib import Path

import pytest
from tomlkit import parse

from somesy.core.core import (
    ProjectMetadata,
    SomesyConfig,
    _extract_cli_config,
    _extract_metadata,
    get_input_content,
    get_project_metadata,
    get_somesy_cli_config,
    validate_somesy_input,
)


@pytest.fixture
def somesy_metadata_only():
    return Path("tests/core/data/.somesy.toml")


@pytest.fixture
def somesy_with_config():
    return Path("tests/core/data/.somesy.with_config.toml")


def test_get_input_content(tmp_path, somesy_metadata_only):
    # test with a file that is not a TOML file
    file = tmp_path / ".somesy.yaml"
    with pytest.raises(ValueError):
        get_input_content(file)

    # with an empty file
    file = tmp_path / ".somesy.toml"
    file.touch()
    with pytest.raises(ValueError):
        get_input_content(file)

    # with a valid pyproject file
    file = Path("tests/core/data/pyproject.toml")
    content = get_input_content(file)
    assert isinstance(content, dict)
    assert "project" in content

    # with a valid somesy file
    content = get_input_content(somesy_metadata_only)
    assert isinstance(content, dict)
    assert "project" in content


def test_extract_metadata(somesy_metadata_only):
    # valid somesy file
    content = get_input_content(somesy_metadata_only)
    metadata = _extract_metadata(content)
    assert isinstance(metadata, ProjectMetadata)
    assert metadata.name == "somesy"
    assert metadata.version == "0.1.0"

    # invalid input with parse
    content = """[project]
    name = "somesy"
    """
    with pytest.raises(ValueError):
        _extract_metadata(parse(content))


def test_extract_cli_config(somesy_with_config, somesy_metadata_only):
    # test with config exists
    content = get_input_content(somesy_with_config)
    config = _extract_cli_config(content)
    assert isinstance(config, SomesyConfig)
    assert config.debug == True

    # test with config does not exist
    content = get_input_content(somesy_metadata_only)
    config = _extract_cli_config(content)
    assert config is None

    # test with invalid input
    content = """[config.cli]
    show_info = 3
    """
    with pytest.raises(ValueError):
        _extract_cli_config(parse(content))


def test_get_project_metadata(somesy_metadata_only):
    metadata = get_project_metadata(somesy_metadata_only)
    assert isinstance(metadata, ProjectMetadata)
    assert metadata.name == "somesy"
    assert metadata.version == "0.1.0"


def test_get_somesy_cli_config(somesy_with_config, somesy_metadata_only):
    # test with config exists
    config = get_somesy_cli_config(somesy_with_config)
    assert isinstance(config, SomesyConfig)
    assert config.debug == True

    # test with config does not exist
    config = get_somesy_cli_config(somesy_metadata_only)
    assert config is None


def test_validate_somesy_input(somesy_metadata_only, somesy_with_config, tmp_path):
    # test with valid input
    validate_somesy_input(somesy_metadata_only)
    validate_somesy_input(somesy_with_config)

    # test with an empty file (not a valid somesy input file)
    input_file = tmp_path / ".somesy.toml"
    input_file.touch()
    result = validate_somesy_input(input_file)
    assert result == False

    # test with invalid config

    input_file.write_text(
        somesy_metadata_only.read_text() + "\n[config.cli]\nshow_info = 3\n"
    )
    result = validate_somesy_input(input_file)
    assert result == False
