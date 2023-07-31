import pytest
from pydantic import ValidationError

from somesy.package_json.models import PackageJsonConfig

base_config = {
    "name": "somesy",
    "version": "0.0.1",
    "description": "A cli tool for synchronizing CITATION.CFF with project files.",
    "keywords": ["react", "javascript"],
    "author": "John Doe <john@doe.com> (http://johndoe.com/)",
    "license": "MIT",
}


@pytest.fixture
def cfg():
    return dict(base_config)


def test_init(cfg):
    # base config runs without an error
    PackageJsonConfig(**base_config)


def test_name(cfg):
    # package names with error
    cfg["name"] = ""
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)

    cfg["name"] = "asd::"
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)


def test_version_reject(cfg):
    # package version with error
    cfg["version"] = ""
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)

    cfg["version"] = "0.0.1..0.2"
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)


def test_license(cfg):
    # without an error
    cfg["license"] = "MIT"
    PackageJsonConfig(**cfg)


def test_author(cfg):
    # author with error
    cfg["author"] = "John Doe <a@a.a>"
    PackageJsonConfig(**cfg)

    cfg["author"] = "John Doe <aa.a>"
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)

    cfg["author"] = "John Doe <a@a.a> (http:/a.a)"
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)

    cfg["author"] = {"name": "John Doe", "email": "a@a.a", "url": "http://a.a"}
    PackageJsonConfig(**cfg)


def test_maintainers_accept(cfg):
    # without an error
    cfg["maintainers"] = ["John Doe <a@a.a>"]
    PackageJsonConfig(**cfg)


def test_maintainers_reject(cfg):
    # maintainers with error
    cfg["maintainers"] = "John Doe <a@a.a>"
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)

    cfg["maintainers"] = ["John Doe <aa.a>"]
    with pytest.raises(ValidationError):
        PackageJsonConfig(**cfg)
