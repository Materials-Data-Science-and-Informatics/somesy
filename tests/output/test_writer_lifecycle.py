"""Regression tests for writer lifecycle (in-memory init) and empty values."""

import pytest

from somesy.cff.writer import CFF
from somesy.codemeta.writer import CodeMeta
from somesy.mkdocs.writer import MkDocs
from somesy.pom_xml.writer import POM
from somesy.rust.writer import Rust


@pytest.mark.parametrize(
    "cls,name", [(CFF, "CITATION.cff"), (CodeMeta, "codemeta.json"), (POM, "pom.xml")]
)
def test_new_file_only_created_by_save(tmp_path, cls, name):
    path = tmp_path / name
    writer = cls(path)
    assert not path.exists()
    writer.save()
    assert path.is_file()
    if cls is not CFF:  # a bare CFF stub lacks required authors/title
        assert cls(path).path == path


def test_pom_new_file_keeps_root_attributes(tmp_path):
    path = tmp_path / "pom.xml"
    POM(path).save()
    text = path.read_text(encoding="utf-8")
    assert "maven.apache.org/POM/4.0.0" in text
    assert "semver-spec" in text


def test_mkdocs_blank_description_not_none_string(tmp_path):
    path = tmp_path / "mkdocs.yml"
    path.write_text("site_name: x\nsite_description:\n", encoding="utf-8")
    writer = MkDocs(path, pass_validation=True)
    writer.save()
    assert "None" not in path.read_text(encoding="utf-8")


def test_cff_empty_file_treated_as_new(tmp_path):
    path = tmp_path / "CITATION.cff"
    path.write_text("", encoding="utf-8")
    writer = CFF(path)
    assert writer._data["cff-version"] == "1.2.0"
    writer.save()
    assert "cff-version" in path.read_text(encoding="utf-8")


def test_cff_comment_only_file_pass_validation(tmp_path):
    path = tmp_path / "CITATION.cff"
    path.write_text("# nothing\n", encoding="utf-8")
    writer = CFF(path, pass_validation=True)
    writer.save()
    assert "cff-version" in path.read_text(encoding="utf-8")


def test_cff_blank_abstract_saves(tmp_path):
    path = tmp_path / "CITATION.cff"
    CFF(path).save()
    text = path.read_text(encoding="utf-8") + "abstract:\n"
    path.write_text(text, encoding="utf-8")
    writer = CFF(path, pass_validation=True)
    writer.save()
    assert path.is_file()


def test_rust_without_package_table(tmp_path):
    path = tmp_path / "Cargo.toml"
    path.write_text('[workspace]\nmembers = ["a"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="package"):
        Rust(path)


def test_mkdocs_empty_file(tmp_path):
    path = tmp_path / "mkdocs.yml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        MkDocs(path)
