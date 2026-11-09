"""Saving a metadata file must never leave a truncated or partial file behind."""

import json
import os
import shutil
import stat
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
import tomlkit
from ruamel.yaml.emitter import Emitter

import somesy.rust.writer as rust_writer
from somesy.cff import CFF
from somesy.codemeta import CodeMeta
from somesy.fortran import Fortran
from somesy.julia import Julia
from somesy.mkdocs import MkDocs
from somesy.package_json import PackageJSON
from somesy.pom_xml.writer import POM
from somesy.pyproject import Pyproject
from somesy.rust import Rust

DATA = Path(__file__).parent.parent / "data"

# (file name, fixture, writer class, serializer kind)
WRITERS: list[tuple[str, str | None, Any, str]] = [
    ("pyproject.toml", "pyproject.toml", Pyproject, "toml"),
    ("Project.toml", "Project.toml", Julia, "toml"),
    ("fpm.toml", "fpm.toml", Fortran, "toml"),
    ("Cargo.toml", "Cargo.toml", Rust, "toml"),
    ("package.json", "package.json", PackageJSON, "json"),
    ("codemeta.json", None, CodeMeta, "json"),
    ("CITATION.cff", "CITATION.cff", CFF, "yaml"),
    ("mkdocs.yml", "mkdocs.yml", MkDocs, "yaml"),
    ("pom.xml", "pom.xml", POM, "xml"),
]


def _boom(*args, **kwargs):
    raise RuntimeError("serializer failed")


def _break_serializer(monkeypatch, kind):
    if kind == "toml":
        for name in ("dump", "dumps"):
            monkeypatch.setattr(tomlkit, name, _boom)
            if hasattr(rust_writer, name):
                monkeypatch.setattr(rust_writer, name, _boom)
    elif kind == "json":
        monkeypatch.setattr(json, "dump", _boom)
        monkeypatch.setattr(json, "dumps", _boom)
    elif kind == "yaml":
        monkeypatch.setattr(Emitter, "emit", _boom)
    else:
        monkeypatch.setitem(ET._serialize, "xml", _boom)


def _prepare(tmp_path, filename, fixture, writer_cls):
    path = tmp_path / filename
    if fixture is None:
        path.write_text(
            json.dumps({"@context": "https://w3id.org/codemeta/3.1", "name": "x"})
        )
    else:
        shutil.copy(DATA / fixture, path)
    return path, writer_cls(path, pass_validation=True)


@pytest.mark.parametrize(("filename", "fixture", "writer_cls", "kind"), WRITERS)
def test_failed_serialization_keeps_original_file(
    tmp_path, monkeypatch, filename, fixture, writer_cls, kind
):
    path, writer = _prepare(tmp_path, filename, fixture, writer_cls)
    before = path.read_bytes()
    _break_serializer(monkeypatch, kind)

    with pytest.raises(RuntimeError, match="serializer failed"):
        writer.save(path)

    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [filename]


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
@pytest.mark.parametrize(("filename", "fixture", "writer_cls", "kind"), WRITERS)
def test_save_preserves_file_mode_and_leaves_no_temp_file(
    tmp_path, filename, fixture, writer_cls, kind
):
    path, writer = _prepare(tmp_path, filename, fixture, writer_cls)
    path.chmod(0o640)

    writer.save(path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    assert sorted(p.name for p in tmp_path.iterdir()) == [filename]


def test_atomic_write_bytes_and_text(tmp_path):
    from somesy.core.core import atomic_write

    target = tmp_path / "a.txt"
    atomic_write(target, "x\ny\n", newline="\n")
    assert target.read_bytes() == b"x\ny\n"
    atomic_write(target, b"\xff\x00")
    assert target.read_bytes() == b"\xff\x00"
    assert [p.name for p in tmp_path.iterdir()] == ["a.txt"]


def test_atomic_write_exclusive_does_not_overwrite(tmp_path):
    from somesy.core.core import atomic_write

    target = tmp_path / "a.txt"
    target.write_text("keep")
    with pytest.raises(FileExistsError):
        atomic_write(target, "new", exclusive=True)
    assert target.read_text() == "keep"
    assert [p.name for p in tmp_path.iterdir()] == ["a.txt"]


def test_write_json_output_is_unchanged(tmp_path):
    from somesy.core.core import write_json

    target = tmp_path / "a.json"
    write_json({"k": "é", "l": [1]}, target)
    assert target.read_bytes() == '{\n  "k": "é",\n  "l": [\n    1\n  ]\n}\n'.encode()


def test_init_config_and_set_value_keep_file_on_failure(
    tmp_path, monkeypatch, create_files, file_types
):
    from somesy.commands.init_config import init_config
    from somesy.commands.set_value import set_project_value

    create_files({(file_types.SOMESY, "somesy.toml")})
    path = tmp_path / "somesy.toml"
    before = path.read_bytes()
    _break_serializer(monkeypatch, "toml")

    with pytest.raises(RuntimeError, match="serializer failed"):
        init_config(path, {"no_sync_cff": True})
    assert path.read_bytes() == before

    with pytest.raises(RuntimeError, match="serializer failed"):
        set_project_value(path, "name", "other")
    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["somesy.toml"]


def test_atomic_write_creates_missing_parent_folders(tmp_path, caplog):
    """Missing parent folders are created and logged at INFO level."""
    from somesy.core.core import atomic_write

    target = tmp_path / "docs" / "nested" / "out.txt"
    with caplog.at_level("INFO", logger="somesy"):
        atomic_write(target, "hello\n")
    assert target.read_text() == "hello\n"
    assert any(
        r.levelname == "INFO" and str(target.parent) in r.getMessage()
        for r in caplog.records
    )
