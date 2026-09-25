"""Validation of PEP 508 package names in pyproject models."""

import pytest
from pydantic import ValidationError

from somesy.pyproject.models import Pep621Config, PoetryConfig


@pytest.mark.parametrize(
    "name",
    [
        "acme.widgets",
        "zope.interface",
        "ruamel.yaml",
        "backports.zoneinfo",
        "test-package",
        "test_package",
        "simple",
    ],
)
def test_pep621_accepts_pep508_names(name):
    cfg = Pep621Config(name=name, version="0.1.0", description="x")
    assert cfg.name == name


@pytest.mark.parametrize(
    "name",
    [
        "acme.widgets",
        "zope.interface",
        "test-package",
    ],
)
def test_poetry_accepts_pep508_names(name):
    cfg = PoetryConfig(
        name=name,
        version="0.1.0",
        description="x",
        license="MIT",
        authors=["Jane Doe <jane@example.com>"],
    )
    assert cfg.name == name


@pytest.mark.parametrize("name", [".leadingdot", "trailingdot.", "-leading"])
def test_pep621_rejects_invalid_names(name):
    with pytest.raises(ValidationError):
        Pep621Config(name=name, version="0.1.0", description="x")
