"""A sync run either writes every target or none of them."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from somesy.codemeta import CodeMeta
from somesy.commands.sync import sync
from somesy.core.models import (
    LicenseEnum,
    Person,
    ProjectMetadata,
    SomesyConfig,
    SomesyInput,
)

NO_OTHERS = {
    f"no_sync_{key}": True
    for key in (
        "pyproject",
        "package_json",
        "julia",
        "fortran",
        "pom_xml",
        "mkdocs",
        "rust",
    )
}


def _metadata() -> ProjectMetadata:
    return ProjectMetadata(
        name="demo",
        version="1.0.0",
        description="Demo project.",
        license=LicenseEnum.MIT,
        people=[
            Person(
                given_names="A", family_names="B", author=True, publication_author=True
            )
        ],
    )


def _input(tmp_path, **config) -> SomesyInput:
    return SomesyInput(
        config=SomesyConfig(
            input_file=tmp_path / "somesy.toml",
            pass_validation=True,
            **NO_OTHERS,
            **config,
        ),
        project=_metadata(),
    )


def _fail_codemeta_sync(monkeypatch, only_below: Path | None = None):
    original = CodeMeta.sync

    def sync_or_fail(self, metadata):
        if only_below is None or only_below in self.path.parents:
            raise RuntimeError("codemeta sync failed")
        original(self, metadata)

    monkeypatch.setattr(CodeMeta, "sync", sync_or_fail)


def test_failure_in_later_target_writes_nothing(tmp_path, monkeypatch):
    _fail_codemeta_sync(monkeypatch)

    with pytest.raises(RuntimeError, match="codemeta sync failed"):
        sync(_input(tmp_path))

    assert not (tmp_path / "CITATION.cff").exists()
    assert not (tmp_path / "codemeta.json").exists()


def test_failure_in_package_writes_nothing_for_root(tmp_path, monkeypatch):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "somesy.toml").write_text(
        "[project]\nname = 'child'\ndescription = 'd'\nlicense = 'MIT'\n"
        "[[project.people]]\ngiven-names = 'A'\nfamily-names = 'B'\nauthor = true\n"
    )
    _fail_codemeta_sync(monkeypatch, only_below=package)

    with pytest.raises(RuntimeError, match="codemeta sync failed"):
        sync(_input(tmp_path, packages=[Path("pkg")]))

    assert not (tmp_path / "CITATION.cff").exists()
    assert not (tmp_path / "codemeta.json").exists()


def test_successful_run_saves_all_targets(
    tmp_path,
):
    sync(_input(tmp_path))
    assert (tmp_path / "CITATION.cff").exists()
    assert (tmp_path / "codemeta.json").exists()


def test_second_merge_sync_does_not_rewrite_codemeta(tmp_path):
    codemeta = tmp_path / "codemeta.json"
    codemeta.write_text(
        json.dumps(
            {
                "@context": "https://w3id.org/codemeta/3.1",
                "@type": "SoftwareSourceCode",
                "name": "demo",
                "dateModified": "2000-01-01",
                "runtimePlatform": "Old 1",
                "downloadUrl": "https://example.com/download",
            }
        )
    )

    def run():
        sync(_input(tmp_path, merge_codemeta=True, no_sync_cff=True))

    run()
    first = codemeta.read_bytes()
    os.utime(codemeta, ns=(10**9, 10**9))

    run()

    assert codemeta.read_bytes() == first
    assert codemeta.stat().st_mtime_ns == 10**9
    data = json.loads(first)
    # the first run changed the file -> modified today
    assert data["dateModified"] == datetime.now(timezone.utc).date().isoformat()
    assert data["runtimePlatform"] == "Old 1"


def _no_tmp_files(tmp_path):
    return not list(tmp_path.rglob(".*.tmp"))


def test_failed_save_rolls_back_written_files(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_bytes(b'[project]\nname = "old"\nversion = "0.0.1"\n')
    original = pyproject.read_bytes()

    def fail_save(self, path):
        raise RuntimeError("codemeta save failed")

    monkeypatch.setattr(CodeMeta, "save", fail_save)
    config = {**NO_OTHERS, "no_sync_pyproject": False}
    somesy_input = SomesyInput(
        config=SomesyConfig(
            input_file=tmp_path / "somesy.toml", pass_validation=True, **config
        ),
        project=_metadata(),
    )

    with pytest.raises(RuntimeError, match="codemeta save failed"):
        sync(somesy_input)

    assert pyproject.read_bytes() == original
    assert not (tmp_path / "CITATION.cff").exists()
    assert not (tmp_path / "codemeta.json").exists()
    assert _no_tmp_files(tmp_path)


@pytest.mark.skipif(os.name != "posix", reason="needs POSIX permissions")
@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores permissions"
)
def test_read_only_directory_rolls_back_earlier_files(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_bytes(b'[project]\nname = "old"\nversion = "0.0.1"\n')
    original = pyproject.read_bytes()
    ro = tmp_path / "ro"
    ro.mkdir()
    package_json = ro / "package.json"
    package_json.write_text('{"name": "old", "version": "0.0.1"}\n')
    package_original = package_json.read_bytes()
    config = {
        **NO_OTHERS,
        "no_sync_pyproject": False,
        "no_sync_package_json": False,
        "package_json_file": package_json,
    }
    somesy_input = SomesyInput(
        config=SomesyConfig(
            input_file=tmp_path / "somesy.toml", pass_validation=True, **config
        ),
        project=_metadata(),
    )

    ro.chmod(0o555)
    try:
        with pytest.raises(PermissionError):
            sync(somesy_input)
    finally:
        ro.chmod(0o755)

    assert pyproject.read_bytes() == original
    assert package_json.read_bytes() == package_original
    assert not (tmp_path / "CITATION.cff").exists()
    assert not (tmp_path / "codemeta.json").exists()
    assert _no_tmp_files(tmp_path)
