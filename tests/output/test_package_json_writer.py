import pytest

from somesy.core.models import Entity, LicenseEnum, Person, ProjectMetadata
from somesy.package_json.writer import PackageJSON


@pytest.fixture
def package_json(load_files, file_types):
    files = load_files([file_types.PACKAGE_JSON])
    return files[file_types.PACKAGE_JSON]


@pytest.fixture
def package_json_file(create_files, file_types):
    return create_files([(file_types.PACKAGE_JSON, "package.json")]) / "package.json"


def test_content_match(package_json: PackageJSON):
    assert package_json.name == "test-package"
    assert (
        package_json.description == "This is a test package for demonstration purposes."
    )
    assert package_json.license == "MIT"
    assert len(package_json.authors) == 1


def test_sync(package_json: PackageJSON, somesy_input: dict):
    package_json.sync(somesy_input.project)
    assert package_json.name == "testproject"
    assert package_json.version == "1.0.0"


def test_save(tmp_path, package_json: PackageJSON):
    # test save with custom path
    custom_path = tmp_path / "package.json"
    package_json.save(custom_path)
    assert custom_path.is_file()
    data = custom_path.read_bytes()
    assert data.endswith(b"}\n")
    assert not data.endswith(b"}\n\n")


def test_from_to_person(person: Person):
    p_person = PackageJSON._from_person(person)
    assert p_person["name"] == person.full_name
    assert p_person["email"] == person.email
    assert p_person["url"] == str(person.orcid)

    p = PackageJSON._to_person(PackageJSON._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email
    assert p.orcid == person.orcid

    # without email
    p = PackageJSON._to_person("John Doe")
    assert p.full_name == "John Doe"

    # if name has no empty space, our algorithm takes it as an entity
    e = PackageJSON._to_person("FZJ")
    assert isinstance(e, Entity)


def test_only_name(package_json: PackageJSON, person: Person):
    package_json._data["author"] = "John Doe"
    package_json._data["maintainers"] = ["Jane Doe"]

    assert len(package_json.authors) == 1
    assert len(package_json.maintainers) == 1

    # merge and see if it works
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
    package_json.sync(pm)

    assert len(package_json.authors) == 1
    assert len(package_json.maintainers) == 1

    assert package_json.authors[0]["name"] == person.full_name
    assert package_json.authors[0]["email"] == person.email
    assert package_json.authors[0]["url"] == str(person.orcid)


def test_person_merge(package_json_file, person: Person):
    pj = PackageJSON(package_json_file)

    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[person.model_copy(update=dict(author=True, publication_author=True))],
    )
    pj.sync(pm)
    pj.save()

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

    # existing author order preserved
    assert pj.authors[0]["name"] == person1b.full_name
    assert pj.authors[0]["email"] == person1b.email

    # authors are not contributors
    assert len(pj.contributors) == 0

    # new person
    person3 = Person(
        given_names="Janice",
        family_names="Doethan",
        email="jane93@gmail.com",
        author=True,
        publication_author=True,
    )
    # john has a new email address
    person1c = person1b.model_copy(update={"email": "john.of.us@qualityland.com"})
    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.publication_author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    pj.sync(pm)
    pj.save()

    assert len(pj.contributors) == 1
    assert len(pj.maintainers) == 1
    assert pj.authors[0]["name"] == person1c.full_name
    assert pj.authors[0]["email"] == person1c.email

    assert pj.contributors[0]["name"] == person2.full_name
    assert pj.contributors[0]["email"] == person2.email


def test_entity_website_saved(package_json_file):
    pj = PackageJSON(package_json_file)
    pm = ProjectMetadata(
        name="proj",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[Person(given_names="Jane", family_names="Doe", author=True)],
        entities=[Entity(name="ACME", website="https://acme.org")],
    )
    pj.sync(pm)
    pj.save()
    pj = PackageJSON(package_json_file)
    assert {"name": "ACME", "url": "https://acme.org/"} in pj.contributors


def test_sync_contributors_only_non_authors(package_json_file):
    pj = PackageJSON(package_json_file)
    pm = ProjectMetadata(
        name="proj",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[
            Person(given_names="Jane", family_names="Doe", author=True),
            Person(given_names="John", family_names="Roe"),
        ],
    )
    pj.sync(pm)
    names = [c["name"] for c in pj.contributors]
    assert "Jane Doe" not in names
    assert "John Roe" in names


def test_to_person_entity_url():
    e = PackageJSON._to_person({"name": "ACME", "url": "https://acme.org"})
    assert isinstance(e, Entity)
    assert str(e.website).startswith("https://acme.org")


def test_to_person_non_orcid_url():
    p = PackageJSON._to_person({"name": "Jane Doe", "url": "https://jane.org"})
    assert isinstance(p, Person)
    assert p.orcid is None


def test_maintainer_without_email_kept():
    from somesy.package_json.models import PackageJsonConfig

    cfg = PackageJsonConfig(
        name="pkg",
        version="1.0.0",
        description="d",
        license="MIT",
        maintainers=[{"name": "Jane Doe"}],
    )
    assert len(cfg.maintainers) == 1


def test_authors_missing(package_json_file):
    pj = PackageJSON(package_json_file)
    pj._data.pop("author", None)
    assert pj.authors == []


def test_further_authors_become_contributors(package_json_file):
    pj = PackageJSON(package_json_file)
    pm = ProjectMetadata(
        name="proj",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[
            Person(given_names="Jane", family_names="Doe", author=True),
            Person(given_names="John", family_names="Roe"),
            Person(given_names="Ann", family_names="Lee", author=True),
            Person(given_names="Bob", family_names="Ray", author=True),
        ],
    )
    pj.sync(pm)
    pj.save()
    pj = PackageJSON(package_json_file)
    assert pj.authors[0]["name"] == "Jane Doe"
    names = [c["name"] for c in pj.contributors]
    assert names == ["Ann Lee", "Bob Ray", "John Roe"]
