"""Fill optional CodeMeta fields from configured project files and Git."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import tomlkit
from defusedxml import ElementTree
from packaging.requirements import Requirement
from tomlkit.exceptions import ParseError

from somesy.git import harvest as harvest_git


def enrich(
    codemeta: dict[str, Any], sources: dict[str, Path | list[Path] | None]
) -> None:
    """Fill CodeMeta fields absent after canonical Somesy synchronization.

    ``codemeta`` already contains data written from somesy.toml.  This function
    therefore only adds optional fields and never replaces an existing value.
    """
    values: dict[str, Any] = {"requirements": [], "languages": [], "runtimes": []}
    for source_type, paths in sources.items():
        for path in _paths(paths):
            if path.is_file():
                _read_source(source_type, path, values)

    _add(codemeta, "readme", values.get("readme"))
    _add(codemeta, "issueTracker", values.get("issueTracker"))
    _add(codemeta, "releaseNotes", values.get("releaseNotes"))
    _add(codemeta, "softwareRequirements", _unique(values["requirements"]))
    _add(codemeta, "programmingLanguage", ", ".join(_unique(values["languages"])))
    _add(codemeta, "runtimePlatform", ", ".join(_unique(values["runtimes"])))

    root = _source_root(sources)
    if root is not None:
        _read_git(root, values)
    for key in (
        "codeRepository",
        "issueTracker",
        "dateCreated",
        "dateModified",
        "version",
    ):
        _add(codemeta, key, values.get(key))


def _paths(paths: Path | list[Path] | None) -> list[Path]:
    if paths is None:
        return []
    return paths if isinstance(paths, list) else [paths]


def _source_root(sources: dict[str, Path | list[Path] | None]) -> Path | None:
    for paths in sources.values():
        if values := _paths(paths):
            return values[0].parent
    return None


def _read_source(source_type: str, path: Path, values: dict[str, Any]) -> None:
    if source_type == "pyproject":
        _read_pyproject(path, values)
    elif source_type == "package_json":
        _read_package_json(path, values)
    elif source_type in {"julia", "fortran", "rust"}:
        _read_toml_project(source_type, path, values)
    elif source_type == "pom_xml":
        _read_pom(path, values)


def _read_pyproject(path: Path, values: dict[str, Any]) -> None:
    data = tomlkit.parse(path.read_text())
    project = data.get("project") or data.get("tool", {}).get("poetry", {})
    if not project:
        return
    values["languages"].append("Python")
    requires_python = project.get("requires-python")
    if requires_python:
        values["runtimes"].append(f"Python {requires_python}")
    urls = project.get("urls", {})
    _urls(urls, values)
    _url(values, "readme", project.get("readme"))

    dependencies = project.get("dependencies", [])
    if isinstance(dependencies, dict):  # Poetry v1
        python = dependencies.pop("python", None)
        if python:
            values["runtimes"].append(f"Python {python}")
        locked = _poetry_lock_versions(path.with_name("poetry.lock"))
        for name, spec in dependencies.items():
            _named_requirement(values, name, _poetry_version(spec), "Python", locked)
        return
    locked = _poetry_lock_versions(path.with_name("poetry.lock"))
    for dependency in dependencies:
        _requirement(values, dependency, "Python", locked)


def _poetry_version(spec: Any) -> str:
    return spec if isinstance(spec, str) else spec.get("version", "")


def _poetry_lock_versions(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        packages = tomlkit.parse(path.read_text()).get("package", [])
        return {_normalise(package["name"]): package["version"] for package in packages}
    except (KeyError, TypeError, ParseError):
        return {}


def _read_package_json(path: Path, values: dict[str, Any]) -> None:
    data = json.loads(path.read_text())
    values["languages"].append("JavaScript")
    if node := data.get("engines", {}).get("node"):
        values["runtimes"].append(f"Node.js {node}")
    bugs = data.get("bugs")
    _url(values, "issueTracker", bugs.get("url") if isinstance(bugs, dict) else bugs)
    for section in ("dependencies", "peerDependencies", "optionalDependencies"):
        for name, version in data.get(section, {}).items():
            _named_requirement(values, name, version, "Node.js")


def _read_toml_project(source_type: str, path: Path, values: dict[str, Any]) -> None:
    data = tomlkit.parse(path.read_text())
    if source_type == "rust":
        package = data.get("package", {})
        values["languages"].append("Rust")
        if version := package.get("rust-version"):
            values["runtimes"].append(f"Rust {version}")
        dependencies = data.get("dependencies", {})
        runtime = "Rust"
    elif source_type == "julia":
        values["languages"].append("Julia")
        if version := data.get("compat", {}).get("julia"):
            values["runtimes"].append(f"Julia {version}")
        dependencies = data.get("deps", {})
        runtime = "Julia"
    else:
        values["languages"].append("Fortran")
        dependencies = data.get("dependencies", {})
        runtime = "Fortran"
    for name, version in dependencies.items():
        _named_requirement(values, name, _poetry_version(version), runtime)


def _read_pom(path: Path, values: dict[str, Any]) -> None:
    root = ElementTree.parse(path).getroot()
    if root is None:
        return
    namespace = root.tag[1:].partition("}")[0] if root.tag.startswith("{") else ""
    prefix = f"{{{namespace}}}" if namespace else ""
    values["languages"].append("Java")
    properties = root.find(f"{prefix}properties")
    if properties is not None:
        for key in (
            "maven.compiler.release",
            "maven.compiler.target",
            "maven.compiler.source",
        ):
            if version := properties.findtext(f"{prefix}{key}"):
                values["runtimes"].append(f"Java {version}")
                break
    for dependency in root.findall(f".//{prefix}dependency"):
        name = dependency.findtext(f"{prefix}artifactId")
        if name:
            version = dependency.findtext(f"{prefix}version") or ""
            _named_requirement(values, name, version, "Java")


def _urls(urls: Any, values: dict[str, Any]) -> None:
    if not isinstance(urls, dict):
        return
    for name, url in urls.items():
        lowered = name.lower()
        if lowered == "issues":
            _url(values, "issueTracker", url)
        elif lowered == "changelog":
            _url(values, "releaseNotes", url)


def _url(values: dict[str, Any], key: str, value: Any) -> None:
    if (
        key not in values
        and isinstance(value, str)
        and urlparse(value).scheme in {"http", "https"}
    ):
        values[key] = value


def _requirement(
    values: dict[str, Any],
    value: str,
    runtime: str,
    locked: dict[str, str] | None = None,
) -> None:
    try:
        requirement = Requirement(value)
    except (TypeError, ValueError):
        match = re.fullmatch(r"((?:@[^/]+/)?[A-Za-z0-9_.-]+)(.*)", value)
        if match is None:
            return
        name, version = match.groups()
    else:
        name, version = requirement.name, str(requirement.specifier)
    _named_requirement(values, name, version, runtime, locked)


def _named_requirement(
    values: dict[str, Any],
    name: str,
    version: Any,
    runtime: str,
    locked: dict[str, str] | None = None,
) -> None:
    version = (locked or {}).get(_normalise(name), str(version))
    values["requirements"].append(
        {
            "@type": "SoftwareApplication",
            "identifier": name,
            "name": name,
            "runtimePlatform": runtime,
            **({"version": version} if version else {}),
        }
    )


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _unique(values: Iterable[Any]) -> list[Any]:
    seen: set[str] = set()
    result = []
    for value in values:
        key = (
            json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value)
        )
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _add(codemeta: dict[str, Any], key: str, value: Any) -> None:
    if key not in codemeta and value not in (None, "", []):
        codemeta[key] = value


def _read_git(root: Path, values: dict[str, Any]) -> None:
    metadata = harvest_git(root)
    if metadata is None:
        return
    repository = metadata.repository
    if repository:
        if match := re.fullmatch(r"git@([^:]+):(.+)", repository):
            repository = f"https://{match[1]}/{match[2]}"
        values["codeRepository"] = repository.removesuffix(".git")
        parsed = urlparse(values["codeRepository"])
        if parsed.netloc in {"github.com", "gitlab.com"}:
            values["issueTracker"] = values["codeRepository"] + "/issues"
    values["dateCreated"] = (
        metadata.date_created.isoformat() if metadata.date_created else None
    )
    values["dateModified"] = (
        metadata.date_modified.isoformat() if metadata.date_modified else None
    )
    values["version"] = metadata.version
