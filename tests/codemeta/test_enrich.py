"""Tests for optional CodeMeta enrichment from project files and Git."""

import subprocess
from datetime import date

import pytest

from somesy.codemeta.enrich import enrich
from somesy.git.models import GitMetadata


def test_enriches_python_metadata_and_uses_locked_direct_versions(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'example'\nrequires-python = '>=3.10'\n"
        "readme = 'https://example.test/readme'\n"
        "dependencies = ['requests>=2', 'rich']\n\n[project.urls]\n"
        "Issues = 'https://example.test/issues'\n"
        "Changelog = 'https://example.test/changelog'\n"
    )
    (tmp_path / "poetry.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {"name": "canonical"}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert codemeta["programmingLanguage"] == "Python"
    assert codemeta["runtimePlatform"] == "Python >=3.10"
    assert codemeta["readme"] == "https://example.test/readme"
    assert codemeta["issueTracker"] == "https://example.test/issues"
    assert codemeta["releaseNotes"] == "https://example.test/changelog"
    assert codemeta["softwareRequirements"] == [
        {
            "@type": "SoftwareApplication",
            "identifier": "requests",
            "name": "requests",
            "runtimePlatform": "Python",
            "version": "2.32.3",
        },
        {
            "@type": "SoftwareApplication",
            "identifier": "rich",
            "name": "rich",
            "runtimePlatform": "Python",
        },
    ]


def test_enrichment_never_overwrites_canonical_codemeta_values(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"engines": {"node": ">=20"}, "dependencies": {"react": "^19"}}'
    )
    codemeta = {
        "name": "from somesy",
        "runtimePlatform": "custom runtime",
        "softwareRequirements": ["custom requirement"],
    }

    enrich(codemeta, {"package_json": tmp_path / "package.json"}, tmp_path)

    assert codemeta["name"] == "from somesy"
    assert codemeta["runtimePlatform"] == "custom runtime"
    assert codemeta["softwareRequirements"] == ["custom requirement"]
    assert codemeta["programmingLanguage"] == "JavaScript"


def test_enriches_other_supported_language_manifests(tmp_path):
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nrust-version = "1.80"\n[dependencies]\nserde = "1"\n'
    )
    (tmp_path / "Project.toml").write_text(
        '[deps]\nExample = "uuid"\nNoCompat = "other-uuid"\n'
        '[compat]\njulia = "1.10"\nExample = "0.5"\n'
    )
    (tmp_path / "fpm.toml").write_text(
        '[dependencies]\nlib = { git = "https://example.test/lib" }\n'
    )
    (tmp_path / "pom.xml").write_text(
        "<project><properties><maven.compiler.release>21</maven.compiler.release></properties><dependencies><dependency><artifactId>junit</artifactId><version>5.11</version></dependency></dependencies></project>"
    )

    codemeta = {}
    enrich(
        codemeta,
        {
            "rust": tmp_path / "Cargo.toml",
            "julia": tmp_path / "Project.toml",
            "fortran": tmp_path / "fpm.toml",
            "pom_xml": tmp_path / "pom.xml",
        },
        tmp_path,
    )

    assert codemeta["programmingLanguage"] == "Rust, Julia, Fortran, Java"
    assert codemeta["runtimePlatform"] == "Rust 1.80, Julia 1.10, Java 21"
    assert {item["name"] for item in codemeta["softwareRequirements"]} == {
        "serde",
        "Example",
        "NoCompat",
        "lib",
        "junit",
    }
    requirements = {item["name"]: item for item in codemeta["softwareRequirements"]}
    assert requirements["Example"]["version"] == "0.5"
    assert "version" not in requirements["NoCompat"]


def test_enriches_missing_dates_and_repository_from_git(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True
        )

    git("init", "-q")
    git("config", "user.name", "Jane Doe")
    git("config", "user.email", "jane@example.com")
    git("config", "commit.gpgsign", "false")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'example'\n")
    git("add", "pyproject.toml")
    git("commit", "-qm", "initial")
    git("tag", "v1.2.3")
    git("remote", "add", "origin", "git@github.com:example/project.git")

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert codemeta["codeRepository"] == "https://github.com/example/project"
    assert codemeta["issueTracker"] == "https://github.com/example/project/issues"
    assert codemeta["version"] == "v1.2.3"
    assert codemeta["dateCreated"] == codemeta["dateModified"]


def test_enrichment_omits_unknown_git_creation_date(tmp_path, mocker):
    path = tmp_path / "pyproject.toml"
    path.write_text("[project]\nname = 'example'\n")
    mocker.patch(
        "somesy.codemeta.enrich.harvest_git",
        return_value=GitMetadata(date_modified=date(2024, 1, 1)),
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": path}, tmp_path)

    assert "dateCreated" not in codemeta
    assert codemeta["dateModified"] == "2024-01-01"


def test_language_file_issue_tracker_takes_priority_over_git(tmp_path, mocker):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        "[project]\nname = 'example'\n[project.urls]\n"
        "Issues = 'https://example.test/issues'\n"
    )
    mocker.patch(
        "somesy.codemeta.enrich.harvest_git",
        return_value=GitMetadata(repository="https://github.com/example/project.git"),
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": path}, tmp_path)

    assert codemeta["issueTracker"] == "https://example.test/issues"


PEP621_PYPROJECT = (
    "[project]\nname = 'example'\nrequires-python = '>=3.10'\n"
    "dependencies = ['requests>=2', 'rich']\n\n"
    "[dependency-groups]\ndev = ['pytest>=8.0']\n\n"
    "[project.optional-dependencies]\nextra = ['httpx>=0.27']\n"
)


def _versions(codemeta):
    return {
        item["name"]: item.get("version") for item in codemeta["softwareRequirements"]
    }


@pytest.mark.parametrize("lock_name", ["uv.lock", "poetry.lock", "pdm.lock"])
def test_uses_exact_versions_from_any_supported_lock_file(tmp_path, lock_name):
    (tmp_path / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / lock_name).write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert _versions(codemeta)["requests"] == "2.32.3"


def test_finds_workspace_lock_file_above_the_package(tmp_path):
    """uv workspace members keep their lock file at the workspace root."""
    member = tmp_path / "packages" / "member"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": member / "pyproject.toml"}, tmp_path)

    assert _versions(codemeta)["requests"] == "2.32.3"


def test_does_not_search_for_lock_files_above_the_project_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": root / "pyproject.toml"}, root)

    assert _versions(codemeta)["requests"] == ">=2"


def test_falls_back_to_declared_specifiers_without_lock_file(tmp_path):
    (tmp_path / "pyproject.toml").write_text(PEP621_PYPROJECT)

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert _versions(codemeta) == {"requests": ">=2", "rich": None}


def test_omits_dependency_groups_and_extras(tmp_path):
    """Development and optional dependencies are not project requirements."""
    (tmp_path / "pyproject.toml").write_text(PEP621_PYPROJECT)

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert set(_versions(codemeta)) == {"requests", "rich"}


@pytest.mark.parametrize(
    "issue_key, changelog_key",
    [
        ("Issues", "Changelog"),
        ("Bug Tracker", "Release Notes"),
        ("bug-tracker", "release_notes"),
    ],
)
def test_maps_common_project_url_spellings(tmp_path, issue_key, changelog_key):
    """PEP 621 does not standardise [project.urls] key names."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'example'\n\n[project.urls]\n"
        f"'{issue_key}' = 'https://example.test/issues'\n"
        f"'{changelog_key}' = 'https://example.test/changelog'\n"
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert codemeta["issueTracker"] == "https://example.test/issues"
    assert codemeta["releaseNotes"] == "https://example.test/changelog"


def test_poetry_v1_dependencies_still_use_the_poetry_lock(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.poetry]\nname = 'example'\n\n[tool.poetry.dependencies]\n"
        "python = '^3.10'\nrequests = '^2.0'\n"
    )
    (tmp_path / "poetry.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert codemeta["runtimePlatform"] == "Python ^3.10"
    assert _versions(codemeta) == {"requests": "2.32.3"}


@pytest.mark.parametrize(
    "lock_directory, expected",
    [("outside", "2.32.3"), ("above", ">=2")],
)
def test_lock_lookup_for_a_pyproject_outside_the_root(
    tmp_path, lock_directory, expected
):
    """Outside the root only the pyproject's own directory is searched."""
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "pyproject.toml").write_text(PEP621_PYPROJECT)
    directory = outside if lock_directory == "outside" else tmp_path
    (directory / "uv.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": outside / "pyproject.toml"}, root)

    assert _versions(codemeta)["requests"] == expected


def test_keeps_locked_versions_when_an_entry_has_no_version(tmp_path):
    """uv omits the version of the project itself when it is dynamic."""
    (tmp_path / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "example"\nsource = { editable = "." }\n\n'
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n\n'
        '[[package]]\nname = "rich"\nversion = "14.2.0"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert _versions(codemeta) == {"requests": "2.32.3", "rich": "14.2.0"}


def test_ignores_malformed_lock_file(tmp_path):
    (tmp_path / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / "uv.lock").write_text("[[package]\nthis is not toml\n")

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert _versions(codemeta)["requests"] == ">=2"


def test_git_history_is_harvested_from_the_package_not_the_project_root(
    tmp_path, mocker
):
    """A package may be its own repository, only shared files come from above."""
    member = tmp_path / "packages" / "member"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )
    harvest = mocker.patch(
        "somesy.codemeta.enrich.harvest_git",
        return_value=GitMetadata(repository="https://example.test/member"),
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": member / "pyproject.toml"}, member, tmp_path)

    # the lock file is shared by the whole project ...
    assert _versions(codemeta)["requests"] == "2.32.3"
    # ... while the Git history belongs to the package
    harvest.assert_called_once_with(member)
    assert codemeta["codeRepository"] == "https://example.test/member"


def test_project_root_defaults_to_the_given_root(tmp_path):
    (tmp_path / "pyproject.toml").write_text(PEP621_PYPROJECT)
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.32.3"\n'
    )

    codemeta = {}
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"}, tmp_path)

    assert _versions(codemeta)["requests"] == "2.32.3"
