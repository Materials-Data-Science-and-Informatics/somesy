"""Tests for the sync functionality."""

from pathlib import Path

from somesy.commands.sync import sync
from somesy.core.models import SomesyInput, SomesyConfig, ProjectMetadata
from somesy.core.models import Person, LicenseEnum


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
