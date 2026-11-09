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


def test_harvest_sources_skips_malformed_sources(
    tmp_path, create_files, file_types, caplog
):
    create_files({(file_types.POETRY, "pyproject.toml")})
    (tmp_path / "pom.xml").write_text("<project><name>broken</project>")
    (tmp_path / "mkdocs.yml").write_text("site_name: [unclosed\n")

    with caplog.at_level("WARNING", logger="somesy"):
        sources = harvest_sources(tmp_path)

    assert [path.name for path, _ in sources] == ["pyproject.toml"]
    assert "pom.xml" in caplog.text
    assert "mkdocs.yml" in caplog.text


def test_harvest_sources_ignores_rust_workspace_values(tmp_path):
    from somesy.merge import merge_metadata

    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "x"\nversion.workspace = true\n'
        "authors.workspace = true\nlicense.workspace = true\n"
        'description = "d"\n'
    )
    sources = harvest_sources(tmp_path)
    assert len(sources) == 1
    content = sources[0][1]
    assert content["name"] == "x"
    assert content["description"] == "d"
    for key in ("version", "authors", "license"):
        assert not content.get(key)
    merged = merge_metadata([c for _, c in sources], None, allow_incomplete=True)
    assert merged.name == "x"


def test_harvest_failure_warning_names_source_and_error(tmp_path, caplog):
    (tmp_path / "pom.xml").write_text("<project><name>broken</project>")
    with caplog.at_level("WARNING", logger="somesy"):
        harvest_sources(tmp_path)
    assert "pom.xml" in caplog.text
    assert "mismatched tag" in caplog.text
