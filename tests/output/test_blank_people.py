"""Blank person entries in existing files (e.g. from `npm init -y`) count as no person."""

import pytest

from somesy.cff import CFF
from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.fortran import Fortran
from somesy.julia import Julia
from somesy.pom_xml.writer import POM
from somesy.pyproject import Pyproject
from somesy.rust import Rust

PEP621 = '[project]\nname = "x"\nversion = "0.1.0"\ndescription = "d"\n{people}\n'
POETRY = (
    '[tool.poetry]\nname = "x"\nversion = "0.1.0"\ndescription = "d"\n{people}\n'
    '[build-system]\nrequires = ["poetry-core"]\nbuild-backend = "poetry.core.masonry.api"\n'
)
CARGO = '[package]\nname = "x"\nversion = "0.1.0"\n{people}\n'
JULIA = 'name = "x"\nversion = "0.1.0"\nuuid = "c8e1f9c6-0b0f-11ec-9a03-0242ac130003"\n{people}\n'
FPM = 'name = "x"\nversion = "0.1.0"\n{people}\n'
POM_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
    "  <developers>\n    {people}\n  </developers>\n</project>\n"
)
CFF_YAML = (
    "cff-version: 1.2.0\ntype: software\nmessage: cite\ntitle: x\nversion: 0.1.0\n"
    "{people}\n"
)

CASES = {
    "pep621-empty-name": (
        Pyproject,
        "pyproject.toml",
        PEP621,
        'authors = [{name = ""}]',
    ),
    "pep621-empty-table": (Pyproject, "pyproject.toml", PEP621, "authors = [{}]"),
    "pep621-maintainers": (
        Pyproject,
        "pyproject.toml",
        PEP621,
        'authors = [{name = ""}]\nmaintainers = [{}]',
    ),
    "poetry1": (Pyproject, "pyproject.toml", POETRY, 'authors = [""]'),
    "poetry1-whitespace": (Pyproject, "pyproject.toml", POETRY, 'authors = ["  "]'),
    "cargo": (Rust, "Cargo.toml", CARGO, 'authors = [""]'),
    "julia": (Julia, "Project.toml", JULIA, 'authors = [""]'),
    "fpm": (Fortran, "fpm.toml", FPM, 'author = ""'),
    "pom-empty-developer": (POM, "pom.xml", POM_XML, "<developer/>"),
    "pom-empty-name": (
        POM,
        "pom.xml",
        POM_XML,
        "<developer><name></name></developer>",
    ),
}


@pytest.mark.parametrize(
    ("cls", "fname", "template", "people"), CASES.values(), ids=CASES
)
def test_blank_people_are_replaced(tmp_path, cls, fname, template, people):
    path = tmp_path / fname
    path.write_text(template.format(people=people), encoding="utf-8")
    pm = ProjectMetadata(
        name="proj",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[
            Person(given_names="Jane", family_names="Doe", author=True),
            Person(given_names="Ann", family_names="Lee", author=True),
        ],
    )
    writer = cls(path)
    writer.sync(pm)
    writer.save()

    writer = cls(path)
    parsed = writer._parse_people(writer.authors)
    assert parsed[0].full_name == "Jane Doe"
    if cls not in (Fortran,):  # fpm.toml has a single author slot
        assert [p.full_name for p in parsed] == ["Jane Doe", "Ann Lee"]
    assert len(parsed) == len(writer.authors)


def test_cff_incomplete_person_is_kept(tmp_path):
    """Regression guard: incomplete CFF people are intentionally kept."""
    path = tmp_path / "CITATION.cff"
    path.write_text(CFF_YAML.format(people="authors:\n  - {}\n"), encoding="utf-8")
    pm = ProjectMetadata(
        name="proj",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[Person(given_names="Jane", family_names="Doe", author=True)],
    )
    writer = CFF(path)
    writer.sync(pm)
    writer.save()
    text = path.read_text(encoding="utf-8")
    assert "given-names: Jane" in text
    assert "- {}" in text
