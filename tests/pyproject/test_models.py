from pathlib import Path

import pytest
from pydantic import ValidationError

from somesy.pyproject.models import PoetryConfig

base_config = {
    "name": "somesy",
    "description": "desc",
    "version": "0.1.1",
    "authors": ["Mustafa Soylu <a@a.a>"],
}


@pytest.fixture
def cfg():
    return dict(base_config)


def test_name(cfg):
    # base config runs without an error
    PoetryConfig(**base_config)

    # package names with error
    cfg["name"] = ""
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["name"] = "asd::"
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)


def test_version_reject(cfg):
    # package version with error
    cfg["version"] = ""
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["version"] = "0.0.1..0.2"
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)


def test_license(cfg):
    # without an error
    cfg["license"] = "MIT"
    PoetryConfig(**base_config)

    # package license with error
    cfg["license"] = "FZJ"
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)


def test_authors(cfg):
    # authors with error
    cfg["authors"] = "Mustafa Soylu <a@a.a>"
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["authors"] = ["Mustafa Soylu a@a.a"]
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["authors"] = ["Mustafa Soylu <aa.a>"]
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)


def test_maintainers_accept(cfg):
    # without an error
    cfg["maintainers"] = ["Mustafa Soylu <a@a.a>"]
    PoetryConfig(**base_config)


def test_maintainers_reject(cfg):
    # maintainers with error
    cfg["maintainers"] = "Mustafa Soylu <a@a.a>"
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["maintainers"] = ["Mustafa Soylu a@a.a"]
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["maintainers"] = ["Mustafa Soylu <aa.a>"]
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)


def test_readme_accept(cfg):
    # without an error
    cfg["readme"] = Path("README.md")
    PoetryConfig(**base_config)

    cfg["readme"] = [Path("README.md")]
    PoetryConfig(**base_config)


def test_readme_reject(cfg):
    # readme with error
    cfg["readme"] = "Mustafa Soylu <a@a.a>"
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)

    cfg["readme"] = ["Readme2.md"]
    with pytest.raises(ValidationError):
        PoetryConfig(**cfg)
