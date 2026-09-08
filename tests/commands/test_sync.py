"""Tests for the sync functionality."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from somesy.cff import CFF
from somesy.codemeta import CodeMeta
from somesy.commands.sync import _semantic_data, _sync_file, sync
from somesy.core.models import (
    LicenseEnum,
    PartialProjectMetadata,
    Person,
    ProjectMetadata,
    SomesyConfig,
    SomesyInput,
)
from somesy.fortran import Fortran
from somesy.julia import Julia
from somesy.mkdocs import MkDocs
from somesy.package_json import PackageJSON
from somesy.pom_xml.writer import POM
from somesy.pom_xml.xmlproxy import XMLProxy
from somesy.pyproject import Pyproject
from somesy.rust import Rust

TARGETS: list[tuple[str, str | None, type[Any]]] = [
    ("pyproject.toml", "pyproject.toml", Pyproject),
    ("Project.toml", "Project.toml", Julia),
    ("fpm.toml", "fpm.toml", Fortran),
    ("Cargo.toml", "Cargo.toml", Rust),
    ("package.json", "package.json", PackageJSON),
    ("codemeta.json", None, CodeMeta),
    ("CITATION.cff", "CITATION.cff", CFF),
    ("mkdocs.yml", "mkdocs.yml", MkDocs),
    ("pom.xml", "pom.xml", POM),
]


def _restyle(path: Path) -> None:
    """Apply valid formatter-only changes and add unrelated content."""
    if path.suffix == ".json":
        data = json.loads(path.read_text())
        data["x-unrelated"] = {"keep": True}
        path.write_text(json.dumps(dict(reversed(data.items())), indent=4) + "\n")
    elif path.suffix == ".xml":
        text = path.read_text().replace("  ", "    ")
        path.write_text(text.replace("<name>", "<!-- formatter marker -->\n<name>", 1))
    else:
        text = path.read_text().replace(" = ", "=").replace(": ", ":    ")
        path.write_text("# formatter marker\n" + text)


def _sync_options(writer_cls, tmp_path: Path) -> dict:
    if writer_cls is CodeMeta:
        return {
            "merge_codemeta": True,
            "codemeta_sources": {},
            "codemeta_root": tmp_path,
        }
    return {}


@pytest.mark.parametrize(("filename", "fixture", "writer_cls"), TARGETS)
def test_sync_preserves_formatter_output_for_every_target(
    tmp_path, filename, fixture, writer_cls
):
    """Formatter-only edits stay byte-identical; real edits still save and reload."""
    metadata = ProjectMetadata(
        name="testproject",
        version="1.0.0",
        description="Project description.",
        keywords=["first", "second"],
        license=LicenseEnum.MIT,
        repository="https://example.com/project",
        homepage="https://example.com",
        people=[
            Person(
                given_names="John",
                family_names="Doe",
                email="john@example.com",
                author=True,
                maintainer=True,
                publication_author=True,
            )
        ],
    )
    path = tmp_path / filename
    if fixture is None:
        path.write_text(
            json.dumps(
                {
                    "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
                    "@type": "SoftwareSourceCode",
                    "author": [],
                    "x-unrelated": {"keep": True},
                }
            )
        )
    else:
        path.write_text((Path("tests/data") / fixture).read_text())

    options = _sync_options(writer_cls, tmp_path)
    _sync_file(metadata, path, writer_cls, pass_validation=True, **options)
    _restyle(path)
    formatted = path.read_bytes()

    _sync_file(metadata, path, writer_cls, pass_validation=True, **options)
    assert path.read_bytes() == formatted

    changed = metadata.model_copy(update={"name": "renamed-project"})
    _sync_file(changed, path, writer_cls, pass_validation=True, **options)
    assert path.read_bytes() != formatted
    if writer_cls is CodeMeta:
        reloaded = writer_cls(path, merge=True, pass_validation=True)
    else:
        reloaded = writer_cls(path, pass_validation=True)
    assert reloaded.name == "renamed-project"
    assert (
        "x-unrelated" in path.read_text()
        if path.suffix == ".json"
        else "formatter marker" in path.read_text()
    )

    _restyle(path)
    reformatted = path.read_bytes()
    _sync_file(changed, path, writer_cls, pass_validation=True, **options)
    assert path.read_bytes() == reformatted


def test_semantic_comparison_preserves_sequence_order():
    assert _semantic_data({"values": [1, 2]}) != _semantic_data({"values": [2, 1]})


def test_xml_semantic_comparison_ignores_formatting_and_comments(tmp_path):
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    first.write_text(
        '<root b="2" a="1"><item>one</item><!-- keep --><item>two</item></root>'
    )
    second.write_text(
        '<root a="1" b="2">\n  <item>one</item>\n  <item>two</item>\n</root>'
    )
    reversed_items = tmp_path / "reversed.xml"
    reversed_items.write_text(
        '<root a="1" b="2"><item>two</item><item>one</item></root>'
    )

    assert _semantic_data(XMLProxy.parse(first)) == _semantic_data(
        XMLProxy.parse(second)
    )
    assert _semantic_data(XMLProxy.parse(first)) != _semantic_data(
        XMLProxy.parse(reversed_items)
    )


def _codemeta_metadata() -> ProjectMetadata:
    return ProjectMetadata(
        name="project",
        description="Project description.",
        license=LicenseEnum.MIT,
        homepage="https://example.com/project",
        people=[Person(given_names="A", family_names="B", author=True)],
    )


def _sync_codemeta(metadata: ProjectMetadata, path: Path, root: Path) -> None:
    _sync_file(
        metadata,
        path,
        CodeMeta,
        pass_validation=True,
        codemeta_sources={},
        codemeta_root=root,
    )


def test_codemeta_overwrite_preserves_formatter_output(tmp_path):
    path = tmp_path / "codemeta.json"
    metadata = _codemeta_metadata()
    _sync_codemeta(metadata, path, tmp_path)
    data = json.loads(path.read_text())
    path.write_text(json.dumps(dict(reversed(data.items())), indent=4) + "\n")
    formatted = path.read_bytes()

    _sync_codemeta(metadata, path, tmp_path)

    assert path.read_bytes() == formatted


def test_codemeta_overwrite_removes_unrelated_content_on_change(tmp_path):
    path = tmp_path / "codemeta.json"
    metadata = _codemeta_metadata()
    _sync_codemeta(metadata, path, tmp_path)
    data = json.loads(path.read_text())
    data["name"] = "stale"
    data["x-unrelated"] = "remove me"
    path.write_text(json.dumps(data))

    _sync_codemeta(metadata, path, tmp_path)

    updated = json.loads(path.read_text())
    assert updated["name"] == "project"
    assert "x-unrelated" not in updated


def test_codemeta_derived_values_converge_after_one_write(tmp_path):
    path = tmp_path / "codemeta.json"
    metadata = _codemeta_metadata()
    _sync_codemeta(metadata, path, tmp_path)
    first = path.read_bytes()

    data = json.loads(first)
    assert data["license"] == ["https://spdx.org/licenses/MIT"]
    assert data["softwareHelp"] == data["url"] == "https://example.com/project"
    _sync_codemeta(metadata, path, tmp_path)
    assert path.read_bytes() == first


def test_codemeta_merge_preserves_authors_missing_from_partial_metadata(tmp_path):
    path = tmp_path / "codemeta.json"
    path.write_text(
        json.dumps(
            {
                "@context": "https://w3id.org/codemeta/3.1",
                "@type": "SoftwareSourceCode",
                "author": [{"@type": "Organization", "name": "Existing Author"}],
            }
        )
    )
    _sync_file(
        PartialProjectMetadata(name="project", license="MIT"),
        path,
        CodeMeta,
        merge_codemeta=True,
        pass_validation=True,
        codemeta_sources={},
    )

    assert json.loads(path.read_text())["author"] == [
        {"@type": "Organization", "name": "Existing Author"}
    ]


def test_sync_file_does_not_rewrite_unchanged_data(tmp_path):
    class NoopWriter:
        def __init__(self, path, **kwargs):
            self._data = {"formatted": True}

        def sync(self, metadata):
            pass

        def save(self, path):
            raise AssertionError("unchanged output should not be saved")

    _sync_file(
        ProjectMetadata(
            name="project",
            description="description",
            license="MIT",
            people=[Person(given_names="A", family_names="B", author=True)],
        ),
        tmp_path / "metadata",
        NoopWriter,
    )


def test_basic_sync(create_files, file_types):
    """Test basic sync of root project metadata."""
    # Create test files
    files = {
        (file_types.SOMESY, "somesy.toml"),
        (file_types.POETRY, "pyproject.toml"),
        (file_types.CITATION, "CITATION.cff"),
    }
    test_dir = create_files(files)

    # Load input file
    input_file = test_dir / "somesy.toml"
    somesy_input = SomesyInput.from_input_file(input_file)

    # Ensure codemeta file is configured
    # somesy_input.config.codemeta_file = test_dir / "codemeta.json"

    # Run sync
    sync(somesy_input)

    # Verify files were created/updated
    assert (test_dir / "CITATION.cff").exists()
    assert (test_dir / "codemeta.json").exists()
    assert (test_dir / "pyproject.toml").exists()


def test_sync_enriches_codemeta_from_configured_pyproject(tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        "[project]\nname = 'example'\ndependencies = ['requests>=2']\n"
        "requires-python = '>=3.10'\n\n[project.urls]\n"
        "Issues = 'https://example.test/issues'\n"
    )
    codemeta_file = tmp_path / "codemeta.json"
    input_data = SomesyInput(
        config=SomesyConfig(
            input_file=tmp_path / "somesy.toml",
            pyproject_file=pyproject_file,
            codemeta_file=codemeta_file,
            no_sync_cff=True,
            no_sync_package_json=True,
            no_sync_julia=True,
            no_sync_fortran=True,
            no_sync_pom_xml=True,
            no_sync_mkdocs=True,
            no_sync_rust=True,
            pass_validation=True,
        ),
        project=ProjectMetadata(
            name="from somesy",
            description="Canonical metadata",
            license=LicenseEnum.MIT,
            people=[Person(given_names="A", family_names="B", author=True)],
        ),
    )

    sync(input_data)

    codemeta = json.loads(codemeta_file.read_text())
    assert codemeta["name"] == "from somesy"
    assert codemeta["issueTracker"] == "https://example.test/issues"
    assert codemeta["runtimePlatform"] == "Python >=3.10"
    assert codemeta["softwareRequirements"][0]["name"] == "requests"


def test_codemeta_enrichment_preserves_canonical_and_merged_values(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True
        )

    git("init", "-q")
    git("config", "user.name", "Jane Doe")
    git("config", "user.email", "jane@example.com")
    git("config", "commit.gpgsign", "false")
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        "[project]\nname = 'example'\ndependencies = ['requests>=2']\n"
    )
    git("add", "pyproject.toml")
    git("commit", "-qm", "initial")
    git("tag", "v1.0.0")
    git("remote", "add", "origin", "git@github.com:git/example.git")

    codemeta_file = tmp_path / "codemeta.json"
    codemeta_file.write_text(
        json.dumps(
            {
                "@context": ["https://doi.org/10.5063/schema/codemeta-2.0"],
                "@type": "SoftwareSourceCode",
                "author": [],
                "downloadUrl": "https://example.test/download",
            }
        )
    )
    input_data = SomesyInput(
        config=SomesyConfig(
            input_file=tmp_path / "somesy.toml",
            pyproject_file=pyproject_file,
            codemeta_file=codemeta_file,
            merge_codemeta=True,
            no_sync_cff=True,
            no_sync_package_json=True,
            no_sync_julia=True,
            no_sync_fortran=True,
            no_sync_pom_xml=True,
            no_sync_mkdocs=True,
            no_sync_rust=True,
            pass_validation=True,
        ),
        project=ProjectMetadata(
            name="from somesy",
            description="Canonical metadata",
            version="9.0.0",
            license=LicenseEnum.MIT,
            repository="https://canonical.example/repository",
            people=[Person(given_names="A", family_names="B", author=True)],
        ),
    )

    sync(input_data)

    codemeta = json.loads(codemeta_file.read_text())
    assert codemeta["codeRepository"] == "https://canonical.example/repository"
    assert codemeta["version"] == "9.0.0"
    assert codemeta["downloadUrl"] == "https://example.test/download"


def test_codemeta_only_sync_still_enriches_from_git(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True
        )

    git("init", "-q")
    git("config", "user.name", "Jane Doe")
    git("config", "user.email", "jane@example.com")
    git("config", "commit.gpgsign", "false")
    git("remote", "add", "origin", "git@github.com:example/project.git")
    (tmp_path / "somesy.toml").write_text("project")
    git("add", "somesy.toml")
    git("commit", "-qm", "initial")

    codemeta_file = tmp_path / "codemeta.json"
    sync(
        SomesyInput(
            config=SomesyConfig(
                input_file=tmp_path / "somesy.toml",
                codemeta_file=codemeta_file,
                no_sync_cff=True,
                no_sync_pyproject=True,
                no_sync_package_json=True,
                no_sync_julia=True,
                no_sync_fortran=True,
                no_sync_pom_xml=True,
                no_sync_mkdocs=True,
                no_sync_rust=True,
                pass_validation=True,
            ),
            project=ProjectMetadata(
                name="from somesy",
                description="Canonical metadata",
                license=LicenseEnum.MIT,
                people=[Person(given_names="A", family_names="B", author=True)],
            ),
        )
    )

    codemeta = json.loads(codemeta_file.read_text())
    assert codemeta["codeRepository"] == "https://github.com/example/project"


def test_package_sync(tmp_path, create_files, file_types):
    """Test sync with package handling."""
    # Create main project structure
    root_dir = tmp_path
    package_dir = root_dir / "package1"
    package_dir.mkdir()

    # Create files in root
    root_files = {
        (file_types.SOMESY, "somesy.toml"),
        (file_types.POETRY, "pyproject.toml"),
    }
    create_files(root_files)

    # Create files in package
    package_files = {
        (file_types.SOMESY, "package1/somesy.toml"),
        (file_types.POETRY, "package1/pyproject.toml"),
    }
    create_files(package_files)

    # Create root config with package
    root_config = SomesyConfig(
        input_file=root_dir / "somesy.toml",
        packages=[Path("package1")],
    )

    # Create root metadata with proper Person fields
    root_metadata = ProjectMetadata(
        name="root-project",
        version="1.0.0",
        description="A test root project",
        license=LicenseEnum.MIT,
        people=[
            Person(
                given_names="Test",
                family_names="Author",
                email="test.author@example.com",
                author=True,
            )
        ],
    )

    root_input = SomesyInput(config=root_config, project=root_metadata)

    # Run sync
    sync(root_input)

    # Verify root files
    assert (root_dir / "CITATION.cff").exists()
    assert (root_dir / "codemeta.json").exists()
    assert (root_dir / "pyproject.toml").exists()

    # Verify package files
    assert (package_dir / "CITATION.cff").exists()
    assert (package_dir / "codemeta.json").exists()
    assert (package_dir / "pyproject.toml").exists()


def test_package_sync_missing_config(tmp_path, create_files, file_types):
    """Test sync with package that has missing configuration."""
    # Create main project structure
    root_dir = tmp_path
    package_dir = root_dir / "package1"
    package_dir.mkdir()

    # Create files in root only
    root_files = {
        (file_types.SOMESY, "somesy.toml"),
        (file_types.POETRY, "pyproject.toml"),
    }
    create_files(root_files)

    # Create root config with package
    root_config = SomesyConfig(
        input_file=root_dir / "somesy.toml",
        packages=[Path("package1")],
        codemeta_file=root_dir / "codemeta.json",
        cff_file=root_dir / "CITATION.cff",
    )

    # Create root metadata with proper Person fields
    root_metadata = ProjectMetadata(
        name="root-project",
        version="1.0.0",
        description="A test root project",
        license=LicenseEnum.MIT,
        people=[
            Person(
                given_names="Test",
                family_names="Author",
                email="test.author@example.com",
                author=True,
            )
        ],
    )

    root_input = SomesyInput(config=root_config, project=root_metadata)

    # Run sync - should not fail but log warning
    sync(root_input)

    # Verify root files exist
    assert (root_dir / "CITATION.cff").exists()
    assert (root_dir / "codemeta.json").exists()
    assert (root_dir / "pyproject.toml").exists()

    # Verify package files don't exist
    assert not (package_dir / "CITATION.cff").exists()
    assert not (package_dir / "codemeta.json").exists()


def test_package_sync_pass_validation_loads_incomplete_input(tmp_path):
    """Apply the root pass-validation setting while loading a package."""
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "somesy.toml").write_text(
        "[project]\nname = 'child'\nlicense = 'MIT'\n"
    )
    root = SomesyInput(
        config=SomesyConfig(
            input_file=tmp_path / "somesy.toml",
            packages=[Path("package")],
            no_sync_cff=True,
            no_sync_pyproject=True,
            no_sync_package_json=True,
            no_sync_julia=True,
            no_sync_fortran=True,
            no_sync_pom_xml=True,
            no_sync_mkdocs=True,
            no_sync_rust=True,
            pass_validation=True,
        ),
        project=_codemeta_metadata(),
    )

    sync(root)

    assert (package_dir / "codemeta.json").exists()


def test_sync_with_flags(create_files, file_types):
    """Test sync with various no_sync flags."""
    # Create test files
    files = {
        (file_types.SOMESY, "somesy.toml"),
        (file_types.POETRY, "pyproject.toml"),
        (file_types.PACKAGE_JSON, "package.json"),
        (file_types.CITATION, "CITATION.cff"),
    }
    test_dir = create_files(files)

    # Create config with some sync flags disabled
    config = SomesyConfig(
        input_file=test_dir / "somesy.toml",
        no_sync_cff=True,
        no_sync_codemeta=True,
        pyproject_file=test_dir / "pyproject.toml",
        package_json_file=test_dir / "package.json",
    )

    # Create metadata with proper Person fields
    metadata = ProjectMetadata(
        name="test-project",
        version="1.0.0",
        description="A test project",
        license=LicenseEnum.MIT,
        people=[
            Person(
                given_names="Test",
                family_names="Author",
                email="test.author@example.com",
                author=True,
            )
        ],
    )

    input_data = SomesyInput(config=config, project=metadata)

    # Run sync
    sync(input_data)

    # Verify CFF and CodeMeta were not created/updated
    assert not (test_dir / "codemeta.json").exists()
    cff_mtime = (test_dir / "CITATION.cff").stat().st_mtime

    # Run sync again with flags enabled
    config.no_sync_cff = False
    config.no_sync_codemeta = False
    sync(input_data)

    # Verify files were created/updated
    assert (test_dir / "codemeta.json").exists()
    assert (test_dir / "CITATION.cff").stat().st_mtime > cff_mtime


def test_sync_merge_codemeta(create_files, file_types):
    """Test sync with merge_codemeta flag."""
    # Create test files
    files = {
        (file_types.SOMESY, "somesy.toml"),
        (file_types.POETRY, "pyproject.toml"),
    }
    test_dir = create_files(files)

    # Create config with merge_codemeta enabled
    config = SomesyConfig(
        input_file=test_dir / "somesy.toml",
        merge_codemeta=True,
        codemeta_file=test_dir / "codemeta.json",
    )

    # Create metadata with proper Person fields
    metadata = ProjectMetadata(
        name="test-project",
        version="1.0.0",
        description="A test project",
        license=LicenseEnum.MIT,
        people=[
            Person(
                given_names="Test",
                family_names="Author",
                email="test.author@example.com",
                author=True,
            )
        ],
    )

    input_data = SomesyInput(config=config, project=metadata)

    # Run sync
    sync(input_data)

    # Verify CodeMeta was created
    assert (test_dir / "codemeta.json").exists()
