"""Tests for optional CodeMeta enrichment from project files and Git."""

import subprocess
from datetime import date

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
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"})

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

    enrich(codemeta, {"package_json": tmp_path / "package.json"})

    assert codemeta["name"] == "from somesy"
    assert codemeta["runtimePlatform"] == "custom runtime"
    assert codemeta["softwareRequirements"] == ["custom requirement"]
    assert codemeta["programmingLanguage"] == "JavaScript"


def test_enriches_other_supported_language_manifests(tmp_path):
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nrust-version = "1.80"\n[dependencies]\nserde = "1"\n'
    )
    (tmp_path / "Project.toml").write_text(
        '[deps]\nExample = "uuid"\n[compat]\njulia = "1.10"\n'
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
    )

    assert codemeta["programmingLanguage"] == "Rust, Julia, Fortran, Java"
    assert codemeta["runtimePlatform"] == "Rust 1.80, Julia 1.10, Java 21"
    assert {item["name"] for item in codemeta["softwareRequirements"]} == {
        "serde",
        "Example",
        "lib",
        "junit",
    }


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
    enrich(codemeta, {"pyproject": tmp_path / "pyproject.toml"})

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
    enrich(codemeta, {"pyproject": path})

    assert "dateCreated" not in codemeta
    assert codemeta["dateModified"] == "2024-01-01"
