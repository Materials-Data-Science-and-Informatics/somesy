"""Tests for project-file metadata harvesting."""

from somesy.harvest import harvest_sources


def test_harvest_sources_uses_existing_endpoint_readers(
    tmp_path, create_files, file_types
):
    create_files(
        {
            (file_types.POETRY, "pyproject.toml"),
            (file_types.PACKAGE_JSON, "package.json"),
        }
    )

    sources = harvest_sources(tmp_path)

    assert [path.name for path, _ in sources] == ["pyproject.toml", "package.json"]
    assert sources[0][1]["name"] == "test-package"
    assert sources[0][1]["people"][0].author is True
    assert sources[1][1]["name"] == "test-package"


def test_harvest_sources_ignores_generated_metadata(tmp_path, create_files, file_types):
    create_files({(file_types.CITATION, "CITATION.cff")})

    assert harvest_sources(tmp_path) == []
