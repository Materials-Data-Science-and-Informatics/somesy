"""Tests for the sync functionality."""

import json
import subprocess
from pathlib import Path

from somesy.commands.sync import _sync_file, sync
from somesy.core.models import (
    LicenseEnum,
    Person,
    ProjectMetadata,
    SomesyConfig,
    SomesyInput,
)


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
