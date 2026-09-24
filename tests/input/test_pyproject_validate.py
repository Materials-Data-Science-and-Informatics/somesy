import pytest
from pydantic import ValidationError
from tomlkit import dump

from somesy.pyproject import Pyproject

VALID_NAMES = [
    "a",
    "7",
    "acme",
    "acme-widgets",
    "acme_widgets",
    "acme.widgets",
    "zope.interface",
    "ruamel.yaml",
    "backports.zoneinfo",
    "acme..widgets",
    "acme--widgets",
    "acme__widgets",
    "acme._-widgets",
    "Acme.Widgets",
]

INVALID_NAMES = [
    "",
    "...",
    ".acme",
    "acme.",
    "-acme",
    "acme-",
    "_acme",
    "acme_",
    " acme",
    "acme ",
    "ac me",
    "ac\tme",
    "acme\n",
    "acmé",
    "acme/widgets",
    "acme@widgets",
    "acme!",
]

# (wrap, authors) per metadata route: PEP 621 people are tables, Poetry v1 accepts plain strings.
PEP621_AUTHORS = [{"name": "John Doe", "email": "john.doe@example.com"}]
POETRY_AUTHORS = ["John Doe <john.doe@example.com>"]
ROUTES = {
    "pep621": (lambda obj: {"project": obj}, PEP621_AUTHORS),
    "poetry-v1": (lambda obj: {"tool": {"poetry": obj}}, POETRY_AUTHORS),
    "poetry-v2": (lambda obj: {"tool": {"poetry": {}}, "project": obj}, PEP621_AUTHORS),
}


@pytest.fixture(params=ROUTES.values(), ids=ROUTES.keys())
def pyproject_route(request):
    """Write a minimal, otherwise-valid pyproject.toml for one metadata route."""
    wrap, authors = request.param

    def _write(tmp_path, name: str):
        obj = {
            "name": name,
            "version": "0.1.0",
            "description": "test package",
            "license": "MIT",
            "authors": authors,
        }
        path = tmp_path / "pyproject.toml"
        with open(path, "w+") as f:
            dump(wrap(obj), f)
        return path

    return _write


@pytest.mark.parametrize("name", VALID_NAMES)
def test_package_name_accepts_dots_and_repeated_separators(
    tmp_path, pyproject_route, name
):
    """PEP 621 and Poetry v1/v2 names allow dots and repeated/mixed separators."""
    path = pyproject_route(tmp_path, name)
    assert Pyproject(path).name == name


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_package_name_rejects_invalid_names(tmp_path, pyproject_route, name):
    """Invalid package names are still rejected, targeting the name field."""
    path = pyproject_route(tmp_path, name)
    with pytest.raises(ValidationError) as exc_info:
        Pyproject(path)
    assert any(err["loc"] == ("name",) for err in exc_info.value.errors())


def test_poetry_validate_accept(load_files, file_types):
    """Validate by loading the data pyproject file using the fixture."""
    load_files([file_types.SETUPTOOLS])
    load_files([file_types.UV])  # PEP 621 without any [tool.poetry]
    load_files([file_types.POETRY])  # Poetry v1
    load_files([file_types.POETRY2])  # Poetry v2


def test_poetry_validate(tmp_path):
    """Test validating a pyproject file in both poetry and PEP 621 formats."""

    # Test Poetry v1 format with invalid values
    reject_poetry_v1_object = {
        "tool": {
            "poetry": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]}
        }
    }
    invalid_poetry_path = tmp_path / "pyproject.toml"
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_poetry_v1_object, f)

    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # Test Poetry v2 format with invalid values
    reject_poetry_v2_object = {
        "tool": {"poetry": {}},
        "project": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]},
    }
    invalid_poetry_path = tmp_path / "pyproject2.toml"
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_poetry_v2_object, f)

    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # if we pass validation, it should not raise an error for either version
    Pyproject(invalid_poetry_path, pass_validation=True)

    # Test PEP 621 [project] format with invalid values
    reject_pep621_object = {
        "project": {"name": "somesy", "version": "abc", "authors": ["John Doe <"]}
    }
    with open(invalid_poetry_path, "w+") as f:
        dump(reject_pep621_object, f)
    with pytest.raises(ValueError):
        Pyproject(invalid_poetry_path)

    # if we pass validation, it should not raise an error
    Pyproject(invalid_poetry_path, pass_validation=True)


def test_dynamic_version_pep621_valid(tmp_path):
    """PEP 621: dynamic = ['version'] without version field should pass validation."""
    obj = {
        "project": {
            "name": "somesy",
            "description": "A test package",
            "dynamic": ["version"],
        }
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    p = Pyproject(path)
    assert "version" in p._dynamic_fields


def test_dynamic_version_poetry2_valid(tmp_path):
    """Poetry v2: dynamic = ['version'] without version field should pass validation."""
    obj = {
        "tool": {"poetry": {}},
        "project": {
            "name": "somesy",
            "description": "A test package",
            "dynamic": ["version"],
            "license": "MIT",
            "authors": [{"name": "John Doe", "email": "john@example.com"}],
        },
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    p = Pyproject(path)
    assert "version" in p._dynamic_fields


def test_missing_version_not_dynamic_pep621_fails(tmp_path):
    """PEP 621: missing version without dynamic should fail validation."""
    obj = {
        "project": {
            "name": "somesy",
            "description": "A test package",
        }
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    with pytest.raises(ValueError, match="version"):
        Pyproject(path)


def test_missing_version_not_dynamic_poetry2_fails(tmp_path):
    """Poetry v2: missing version without dynamic should fail validation."""
    obj = {
        "tool": {"poetry": {}},
        "project": {
            "name": "somesy",
            "description": "A test package",
            "license": "MIT",
            "authors": [{"name": "John Doe", "email": "john@example.com"}],
        },
    }
    path = tmp_path / "pyproject.toml"
    with open(path, "w+") as f:
        dump(obj, f)

    with pytest.raises(ValueError, match="version"):
        Pyproject(path)
