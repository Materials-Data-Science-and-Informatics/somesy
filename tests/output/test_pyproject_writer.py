import logging
from pathlib import Path

import pytest
import tomlkit

from somesy.core.models import Entity, LicenseEnum, Person, ProjectMetadata
from somesy.pyproject.writer import Pep621, Poetry, Pyproject


@pytest.fixture
def pyproject_poetry(load_files, file_types):
    files = load_files([file_types.POETRY])
    return files[file_types.POETRY]


@pytest.fixture
def pyproject_poetry2(load_files, file_types):
    files = load_files([file_types.POETRY2])
    return files[file_types.POETRY2]


@pytest.fixture
def pyproject_poetry_file(create_files, file_types):
    folder = create_files([(file_types.POETRY, "pyproject.toml")])
    return folder / Path("pyproject.toml")


@pytest.fixture
def pyproject_poetry2_file(create_files, file_types):
    folder = create_files([(file_types.POETRY2, "pyproject2.toml")])
    return folder / Path("pyproject2.toml")


@pytest.fixture
def pyproject_setuptools(load_files, file_types):
    files = load_files([file_types.SETUPTOOLS])
    return files[file_types.SETUPTOOLS]


@pytest.fixture
def pyproject_setuptools_file(create_files, file_types):
    folder = create_files([(file_types.SETUPTOOLS, "pyproject.toml")])
    return folder / Path("pyproject.toml")


@pytest.fixture
def pyproject_uv(load_files, file_types):
    files = load_files([file_types.UV])
    return files[file_types.UV]


@pytest.fixture
def pyproject_uv_file(create_files, file_types):
    folder = create_files([(file_types.UV, "pyproject.toml")])
    return folder / Path("pyproject.toml")


def test_content_match(
    pyproject_poetry, pyproject_poetry2, pyproject_setuptools, pyproject_uv
):
    # create a function to check both file formats
    def assert_content_match(pyproject_file):
        assert pyproject_file.name == "test-package"
        assert (
            pyproject_file.description
            == "This is a test package for demonstration purposes."
        )
        license_text = pyproject_file.license
        if isinstance(license_text, dict):
            license_text = license_text["text"]
        if isinstance(license_text, str):
            assert license_text == "MIT"
        else:
            assert license_text.text.value == "MIT"
        assert len(pyproject_file.authors) == 1

    # assert for all formats
    assert_content_match(pyproject_poetry)
    assert_content_match(pyproject_poetry2)
    assert_content_match(pyproject_setuptools)
    assert_content_match(pyproject_uv)


def test_sync(
    pyproject_poetry,
    pyproject_poetry2,
    pyproject_setuptools,
    pyproject_uv,
    somesy_input,
):
    def assert_sync(pyproject):
        pyproject.sync(somesy_input.project)
        assert pyproject.name == "testproject"
        assert pyproject.version == "1.0.0"

    assert_sync(pyproject_poetry)
    assert_sync(pyproject_poetry2)
    assert_sync(pyproject_setuptools)
    assert_sync(pyproject_uv)


@pytest.mark.parametrize(
    "writer_fixture, writer_class, version",
    [
        ("pyproject_poetry2_file", Poetry, 2),
        ("pyproject_setuptools_file", Pep621, None),
        ("pyproject_uv_file", Pep621, None),
    ],
)
def test_issue_121_writes_modern_license_string(
    request, writer_fixture, writer_class, version, somesy_input
):
    path = request.getfixturevalue(writer_fixture)
    writer = writer_class(path, version=version) if version else writer_class(path)
    writer.sync(somesy_input.project)
    assert writer._data["project"]["license"] == "MIT"


@pytest.mark.parametrize(
    "writer_fixture, writer_class, version",
    [
        ("pyproject_poetry2_file", Poetry, 2),
        ("pyproject_setuptools_file", Pep621, None),
        ("pyproject_uv_file", Pep621, None),
    ],
)
def test_issue_121_writes_multiple_license_expression(
    request, writer_fixture, writer_class, version, somesy_input
):
    path = request.getfixturevalue(writer_fixture)
    writer = writer_class(path, version=version) if version else writer_class(path)
    somesy_input.project.license = [LicenseEnum.MIT, LicenseEnum.Apache_2_0]
    writer.sync(somesy_input.project)
    assert writer._data["project"]["license"] == "MIT OR Apache-2.0"


def test_save(
    tmp_path, pyproject_poetry, pyproject_poetry2, pyproject_setuptools, pyproject_uv
):
    def assert_save(pyproject):
        custom_path = tmp_path / Path("pyproject.toml")
        pyproject.save(custom_path)
        assert custom_path.is_file()
        custom_path.unlink()

    assert_save(pyproject_poetry)
    assert_save(pyproject_poetry2)
    assert_save(pyproject_setuptools)
    assert_save(pyproject_uv)


def test_from_to_person(person):
    # test for poetry
    assert Poetry._from_person(person) == f"{person.full_name} <{person.email}>"

    p = Poetry._to_person(Poetry._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email

    p = Poetry._to_person("John Doe")
    assert p.given_names == "John"
    assert p.family_names == "Doe"

    e = Poetry._to_person("Entity")
    assert isinstance(e, Entity)
    assert e.name == "Entity"

    # test for PEP 621 [project]
    assert Pep621._from_person(person) == {
        "name": person.full_name,
        "email": person.email,
    }

    p = Pep621._to_person(Pep621._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email


@pytest.mark.parametrize(
    "writer_class, writer_file_fixture, version",
    [
        (Poetry, "pyproject_poetry_file", 1),
        (Poetry, "pyproject_poetry2_file", 2),
        (Pep621, "pyproject_setuptools_file", None),
        (Pep621, "pyproject_uv_file", None),
    ],
)
def test_person_merge_pyproject(
    request, writer_class, writer_file_fixture, version, person
):
    # get suitable project file
    writer_file = request.getfixturevalue(writer_file_fixture)

    # Initialize with correct version for Poetry
    if writer_class == Poetry:
        pj = writer_class(writer_file, version=version)
    else:
        pj = writer_class(writer_file)

    # update project file with known data
    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[person.model_copy(update=dict(author=True, publication_author=True))],
    )
    pj.sync(pm)
    pj.save()
    # ----

    # jane becomes john -> modified person
    person1b = person.model_copy(
        update={"given_names": "John", "author": True, "publication_author": True}
    )

    # different Jane Doe with different orcid -> new person
    person2 = person.model_copy(
        update={
            "orcid": "https://orcid.org/4321-0987-3231",
            "email": "i.am.jane@doe.com",
            "author": True,
            "publication_author": True,
        }
    )
    # use different order, just for some difference
    person2.set_key_order(["given_names", "orcid", "family_names", "email"])

    # listed in "arbitrary" order in somesy metadata (new person comes first)
    pm.people = [person2, person1b]  # need to assign like that to keep _key_order
    pj.sync(pm)
    pj.save()

    # existing author info preserved, order not preserved because no orcid
    if version is not None:
        person1b_rep = writer_class._from_person(person1b, poetry_version=version)
        person2_rep = writer_class._from_person(person2, poetry_version=version)
    else:
        person1b_rep = writer_class._from_person(person1b)
        person2_rep = writer_class._from_person(person2)
    assert (pj.authors[0] == person1b_rep) or (pj.authors[1] == person1b_rep)
    assert (pj.authors[0] == person2_rep) or (pj.authors[1] == person2_rep)

    # new person
    person3 = Person(
        given_names="Janice",
        family_names="Doethan",
        email="jane93@gmail.com",
        author=True,
        publication_author=True,
    )
    if version is not None:
        person3_rep = writer_class._from_person(person3, poetry_version=version)
    else:
        person3_rep = writer_class._from_person(person3)

    # john has a new email address
    person1c = person1b.model_copy(update={"email": "john.of.us@qualityland.com"})
    if version is not None:
        person1c_rep = writer_class._from_person(person1c, poetry_version=version)
    else:
        person1c_rep = writer_class._from_person(person1c)

    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.publication_author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    pj.sync(pm)
    pj.save()

    assert len(pj.maintainers) == 1
    assert pj.authors[0] == person1c_rep
    assert pj.authors[1] == person3_rep


def _unrelated_tables(doc: tomlkit.TOMLDocument) -> dict:
    """Tables sync never touches: build-system, and tool.* other than tool.poetry.

    tool.poetry holds the metadata itself for Poetry v1 fixtures, so it is
    excluded rather than being unrelated content.
    """
    tool = dict(doc.get("tool", {}))
    tool.pop("poetry", None)
    return {"build-system": doc.get("build-system"), "tool": tool}


@pytest.mark.parametrize(
    "writer_fixture",
    [
        "pyproject_poetry_file",
        "pyproject_poetry2_file",
        "pyproject_setuptools_file",
        "pyproject_uv_file",
    ],
)
def test_dotted_name_round_trips_through_save_and_reload(
    request, writer_fixture, somesy_input
):
    """A dotted name survives sync/save/reload, leaving unrelated tables untouched."""
    path = request.getfixturevalue(writer_fixture)
    before = _unrelated_tables(tomlkit.parse(path.read_text()))

    somesy_input.project.name = "Acme.Widgets"
    pyproject = Pyproject(path)
    pyproject.sync(somesy_input.project)
    pyproject.save()

    after = tomlkit.parse(path.read_text())
    assert _unrelated_tables(after) == before

    reloaded = Pyproject(path)
    assert reloaded.name == "Acme.Widgets"
    assert reloaded.version == somesy_input.project.version
    assert reloaded.description == somesy_input.project.description


def test_without_email(tmp_path, person):
    # Test Poetry v1
    pyproject_v1_str = """
    [tool.poetry]
    name = "ttt"
    version = "0.1.0"
    description = "asd"
    authors = ["John Doe"]
    license = "MIT"

    [tool.poetry.dependencies]
    python = "^3.10"

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"
    """

    # Test Poetry v2
    pyproject_v2_str = """
    [tool.poetry]
    name = "ttt"
    version = "0.1.0"
    description = "asd"
    authors = ["John Doe"]
    license = "MIT"

    [project]
    name = "ttt"
    version = "0.1.0"
    description = "asd"
    authors = ["John Doe"]
    license = "MIT"

    [tool.poetry.dependencies]
    python = "^3.10"

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"
    """

    # Test both versions
    for pyproject_str, version in [(pyproject_v1_str, 1), (pyproject_v2_str, 2)]:
        # save to file
        pyproject_file = tmp_path / Path(f"pyproject_v{version}.toml")
        pyproject_file.write_text(pyproject_str)

        # load and sync
        p = Poetry(pyproject_file, version=version)
        assert len(p.authors) == 1

        pm = ProjectMetadata(
            name="My awesome project",
            description="Project description",
            license=LicenseEnum.MIT,
            version="0.1.0",
            people=[
                person.model_copy(
                    update=dict(author=True, publication_author=True, maintainer=True)
                )
            ],
        )

        p.sync(pm)

        assert len(p.authors) == 1
        assert len(p.maintainers) == 1


def test_dynamic_version_not_synced_setuptools(tmp_path, caplog):
    """PEP 621: version listed as dynamic should not be written during sync."""
    pyproject_str = """\
[project]
name = "test-pkg"
description = "A test"
dynamic = ["version"]
authors = [{ name = "John Doe", email = "john@example.com" }]
license = { text = "MIT" }

[build-system]
requires = ["setuptools", "setuptools-scm"]
build-backend = "setuptools.build_meta"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(pyproject_str)

    st = Pep621(path)
    assert "version" in st._dynamic_fields

    pm = ProjectMetadata(
        name="test-pkg",
        description="A test",
        license=LicenseEnum.MIT,
        version="1.0.0",
        people=[
            Person(
                given_names="John",
                family_names="Doe",
                email="john@example.com",
                author=True,
            )
        ],
    )
    with caplog.at_level(logging.WARNING, logger="somesy"):
        st.sync(pm)

    assert (
        "version" not in st._data["project"]
        or st._data["project"].get("version") is None
    )
    assert "dynamic" in caplog.text


def test_dynamic_version_not_synced_poetry2(tmp_path, caplog):
    """Poetry v2: version listed as dynamic should not be written during sync."""
    pyproject_str = """\
[project]
name = "test-pkg"
description = "A test"
dynamic = ["version"]
authors = [{ name = "John Doe", email = "john@example.com" }]
license = "MIT"

[tool.poetry.dependencies]
python = "^3.10"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(pyproject_str)

    p = Poetry(path, version=2)
    assert "version" in p._dynamic_fields

    pm = ProjectMetadata(
        name="test-pkg",
        description="A test",
        license=LicenseEnum.MIT,
        version="1.0.0",
        people=[
            Person(
                given_names="John",
                family_names="Doe",
                email="john@example.com",
                author=True,
            )
        ],
    )
    with caplog.at_level(logging.WARNING, logger="somesy"):
        p.sync(pm)

    assert (
        "version" not in p._data["project"] or p._data["project"].get("version") is None
    )
    assert "dynamic" in caplog.text


UV_PYPROJECT = """\
[project]
name = "test-pkg"
version = "0.1.0"
description = "A test"
authors = [{ name = "John Doe", email = "john@example.com" }]
requires-python = ">=3.10"
dependencies = ["packaging>=24.0"]

[build-system]
requires = ["uv_build>=0.12.13,<0.13.0"]
build-backend = "uv_build"

[tool.uv]
package = true

[tool.uv.sources]
some-dependency = { workspace = true }

[dependency-groups]
dev = ["pytest>=8.0"]
"""

HATCHLING_PYPROJECT = """\
[project]
name = "test-pkg"
description = "A test"
dynamic = ["version"]
authors = [{ name = "John Doe", email = "john@example.com" }]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/test_pkg/__about__.py"
"""

FLIT_PYPROJECT = """\
[project]
name = "test-pkg"
version = "0.1.0"
description = "A test"
authors = [{ name = "John Doe", email = "john@example.com" }]

[build-system]
requires = ["flit_core>=3.4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "test_pkg"
"""

PDM_PYPROJECT = """\
[project]
name = "test-pkg"
version = "0.1.0"
description = "A test"
authors = [{ name = "John Doe", email = "john@example.com" }]

[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[tool.pdm.dev-dependencies]
test = ["pytest>=8.0"]
"""


@pytest.fixture
def metadata(person) -> ProjectMetadata:
    """Return metadata to sync into a project file."""
    return ProjectMetadata(
        name="testproject",
        description="Project description",
        license=LicenseEnum.MIT,
        version="1.0.0",
        people=[person.model_copy(update=dict(author=True, publication_author=True))],
    )


@pytest.mark.parametrize(
    "content",
    [UV_PYPROJECT, HATCHLING_PYPROJECT, FLIT_PYPROJECT, PDM_PYPROJECT],
    ids=["uv", "hatchling", "flit", "pdm"],
)
def test_pep621_backends_use_project_handler(tmp_path, content):
    """Any backend storing metadata in [project] is handled by Pep621, not Poetry."""
    path = tmp_path / "pyproject.toml"
    path.write_text(content)

    assert isinstance(Pyproject(path).__wrapped__, Pep621)


@pytest.mark.parametrize(
    "content",
    [UV_PYPROJECT, HATCHLING_PYPROJECT, FLIT_PYPROJECT, PDM_PYPROJECT],
    ids=["uv", "hatchling", "flit", "pdm"],
)
def test_sync_leaves_backend_specific_tables_untouched(tmp_path, content, metadata):
    """Sync only writes inside [project], never into backend or dependency tables."""
    path = tmp_path / "pyproject.toml"
    path.write_text(content)
    before = tomlkit.parse(content)

    pyproject = Pyproject(path)
    pyproject.sync(metadata)
    pyproject.save()

    after = tomlkit.parse(path.read_text())
    assert after["project"]["name"] == "testproject"
    for table in ("build-system", "tool", "dependency-groups"):
        if table in before:
            assert after[table] == before[table]
    # dependencies are declared in [project] but are not somesy's to manage
    if "dependencies" in before["project"]:
        assert after["project"]["dependencies"] == before["project"]["dependencies"]


def test_ambiguous_pyproject_names_both_metadata_tables(tmp_path):
    """A file without [project] and without [tool.poetry] cannot be handled."""
    path = tmp_path / "pyproject.toml"
    path.write_text('[build-system]\nrequires = ["hatchling"]\n')

    with pytest.raises(ValueError, match=r"\[project\].*\[tool\.poetry\]"):
        Pyproject(path)


def test_dynamic_version_not_synced_hatchling(tmp_path, caplog, metadata):
    """Hatchling: a version computed by the backend is not overwritten."""
    path = tmp_path / "pyproject.toml"
    path.write_text(HATCHLING_PYPROJECT)

    pyproject = Pyproject(path)
    assert "version" in pyproject._dynamic_fields

    with caplog.at_level(logging.WARNING, logger="somesy"):
        pyproject.sync(metadata)

    assert "version" not in pyproject._data["project"]
    assert "dynamic" in caplog.text


@pytest.mark.parametrize(
    "declaration, expected",
    [
        ('license = "MIT"', "MIT"),  # PEP 639 expression
        ('license = { text = "MIT" }', "MIT"),  # deprecated PEP 621 table
        ('license = { file = "LICENSE" }', None),  # file, not an identifier
        ("", None),
    ],
)
def test_reads_license_from_both_pep621_spellings(tmp_path, declaration, expected):
    """Files predating PEP 639 still declare the license as a table."""
    path = tmp_path / "pyproject.toml"
    path.write_text(
        f'[project]\nname = "test-pkg"\nversion = "0.1.0"\n'
        f'description = "A test"\n{declaration}\n'
    )

    assert Pyproject(path).license == expected


def test_harvest_metadata_from_uv_project(pyproject_uv_file):
    """Harvested metadata is usable as somesy input, e.g. by `somesy init`."""
    harvested = Pyproject(pyproject_uv_file).harvest_metadata()

    assert harvested["name"] == "test-package"
    assert harvested["license"] == "MIT"
    assert harvested["homepage"] == "https://example.com/test-package"
    assert harvested["people"][0].email == "john.doe@example.com"


@pytest.mark.parametrize("spelling", ["Homepage", "homepage", "home-page", "HOMEPAGE"])
def test_updates_existing_project_url_whatever_its_spelling(
    tmp_path, spelling, metadata
):
    """PEP 621 leaves [project.urls] key names to the project, so both the
    harvested value and the update must follow the spelling already in use.
    """
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "test-pkg"\nversion = "0.1.0"\n'
        'description = "A test"\n\n[project.urls]\n'
        f'{spelling} = "https://example.com/old"\n'
    )

    pyproject = Pyproject(path)
    assert pyproject.homepage == "https://example.com/old"

    metadata.homepage = "https://example.com/new"
    pyproject.sync(metadata)
    pyproject.save()

    urls = tomlkit.parse(path.read_text())["project"]["urls"]
    assert dict(urls) == {spelling: "https://example.com/new"}


def test_leftover_poetry_configuration_does_not_claim_the_project(tmp_path, metadata):
    """A project migrated to another backend may keep [tool.poetry] sections."""
    path = tmp_path / "pyproject.toml"
    path.write_text(
        HATCHLING_PYPROJECT
        + '\n[tool.poetry.group.dev.dependencies]\npytest = "^8.0"\n'
    )

    pyproject = Pyproject(path)

    assert isinstance(pyproject.__wrapped__, Pep621)
    pyproject.sync(metadata)
    assert pyproject._data["project"]["name"] == "testproject"


def test_poetry_v2_project_is_still_handled_by_poetry(pyproject_poetry2_file):
    """Poetry 2.x keeps its metadata in [project] but is built by Poetry."""
    assert isinstance(Pyproject(pyproject_poetry2_file).__wrapped__, Poetry)


@pytest.mark.parametrize(
    "writer_fixture", ["pyproject_uv_file", "pyproject_poetry2_file"]
)
def test_deprecated_license_table_is_read_as_an_expression(
    request, tmp_path, writer_fixture
):
    """Files predating PEP 639 declare the license as a table, in every flavor."""
    path = request.getfixturevalue(writer_fixture)
    data = tomlkit.parse(path.read_text())
    license = tomlkit.inline_table()
    license["text"] = "MIT"
    data["project"]["license"] = license
    path.write_text(tomlkit.dumps(data))

    assert Pyproject(path).license == "MIT"


@pytest.mark.parametrize(
    "existing, expected_key",
    [
        ("Homepage", "Repository"),  # capitalized table, follow it
        ("homepage", "repository"),  # lowercase table, follow it
        (None, "repository"),  # nothing to follow, somesy's own spelling
    ],
    ids=["capitalized", "lowercase", "empty"],
)
def test_added_project_url_follows_the_style_of_the_table(
    tmp_path, existing, expected_key, metadata
):
    """A table written by a template is uniformly capitalized, keep it that way."""
    urls = (
        f'\n[project.urls]\n{existing} = "https://example.com/hp"\n' if existing else ""
    )
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "test-pkg"\nversion = "0.1.0"\ndescription = "A test"\n'
        + urls
    )

    metadata.repository = "https://github.com/example/test-pkg"
    pyproject = Pyproject(path)
    pyproject.sync(metadata)
    pyproject.save()

    urls_after = tomlkit.parse(path.read_text())["project"]["urls"]
    assert expected_key in urls_after
    assert urls_after[expected_key] == "https://github.com/example/test-pkg"
