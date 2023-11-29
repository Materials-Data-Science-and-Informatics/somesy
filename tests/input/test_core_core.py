import sys
from datetime import datetime
from pathlib import Path

import pytest

from somesy.core.core import discover_input
from somesy.core.models import ProjectMetadata, SomesyConfig
from somesy.core.types import ContributionTypeEnum, LicenseEnum


def test_discover_input(create_files, file_types, monkeypatch: pytest.MonkeyPatch):
    tmp_path = create_files(
        [
            (file_types.SOMESY, "somesy.toml"),
            (file_types.POETRY, "pyproject.toml"),
            (file_types.PACKAGE_JSON, "package.json"),
        ]
    )

    # Test 1: input is given and exists

    # 1.a somesy input file
    somesy_file = tmp_path / Path("somesy.toml")
    result = discover_input(somesy_file)
    assert result == somesy_file

    # 1.b pyproject input file
    pyproject_file = tmp_path / Path("pyproject.toml")
    result = discover_input(pyproject_file)
    assert result == pyproject_file

    # 1.c package.json file
    package_json_file = tmp_path / Path("package.json")
    result = discover_input(package_json_file)
    assert result == package_json_file

    # Test 2: input is given but does not exist, instead default exists and selected
    input_file = tmp_path / Path("somesy2.toml")
    result = discover_input(input_file)
    assert result == Path(".somesy.toml")

    # Test 3: should raise an error when given file or defaults dont exist
    if sys.platform == "win32":
        monkeypatch.chdir(Path("C:\\"))
    else:
        monkeypatch.chdir(Path("/tmp"))
    input_file = Path("/tmp/somesy.toml")
    with pytest.raises(FileNotFoundError):
        discover_input(input_file)


def test_somesy_input(somesy_input):
    # test config inputs
    assert isinstance(somesy_input.config, SomesyConfig)
    assert somesy_input.config.debug is True
    assert somesy_input.config.verbose is False
    assert somesy_input.config.show_info is False
    assert somesy_input.config.no_sync_cff is False
    assert somesy_input.config.cff_file == Path("CITATION.cff")
    assert somesy_input.config.no_sync_pyproject is False
    assert somesy_input.config.pyproject_file == Path("pyproject.toml")
    assert somesy_input.config.no_sync_codemeta is False
    assert somesy_input.config.codemeta_file == Path("codemeta.json")
    assert somesy_input.config.no_sync_package_json is False

    # test project inputs
    assert isinstance(somesy_input.project, ProjectMetadata)
    assert somesy_input.project.name == "testproject"
    assert somesy_input.project.version == "1.0.0"
    assert (
        somesy_input.project.description
        == "This is a test project for demonstration purposes."
    )
    assert somesy_input.project.keywords == ["test", "demo", "example"]
    assert somesy_input.project.license == LicenseEnum.MIT
    assert (
        str(somesy_input.project.repository) == "https://github.com/example/testproject"
    )
    assert str(somesy_input.project.homepage) == "https://example.com/testproject"
    assert len(somesy_input.project.people) == 3
    authors = somesy_input.project.authors()
    assert authors[0].family_names == "Doe"
    assert authors[0].given_names == "John"
    assert authors[0].email == "john.doe@example.com"
    assert str(authors[0].orcid) == "https://orcid.org/0000-0000-0000-0000"
    assert authors[0].contribution == "The main developer, maintainer, and tester."
    assert (
        authors[0].contribution_begin
        == datetime.strptime("2023-01-15", "%Y-%m-%d").date()
    )
    assert authors[0].contribution_types == [
        ContributionTypeEnum.maintenance,
        ContributionTypeEnum.code,
        ContributionTypeEnum.test,
        ContributionTypeEnum.review,
        ContributionTypeEnum.doc,
    ]

    # check publication author
    assert authors[1].publication_author is True
