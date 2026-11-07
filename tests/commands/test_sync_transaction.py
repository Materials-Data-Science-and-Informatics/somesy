"""A sync run either writes every target or none of them."""

import json
import os
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
    assert data["dateModified"] == "2000-01-01"
    assert data["runtimePlatform"] == "Old 1"
