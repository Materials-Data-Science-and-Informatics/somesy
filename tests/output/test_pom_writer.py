import pytest

from somesy.core.models import Entity, LicenseEnum, Person, ProjectMetadata
from somesy.pom_xml.writer import POM


@pytest.fixture
def pom(load_files, file_types):
    files = load_files([file_types.POM_XML])
    return files[file_types.POM_XML]


@pytest.fixture
def pom_file(create_files, file_types):
    return create_files([(file_types.POM_XML, "pom.xml")]) / "pom.xml"


def test_content_match(pom: POM):
    assert pom.name == "test-package"
    assert pom.description == "This is a test package for demonstration purposes."
    assert pom.license == ["MIT", "Apache-2.0"]
    assert len(pom.authors) == 1


def test_sync(pom: POM, somesy_input: dict):
    pom.sync(somesy_input.project)
    assert pom.name == "testproject"
    assert pom.version == "1.0.0"


def test_multiple_licenses(pom: POM, somesy_input):
    somesy_input.project.license = [LicenseEnum.MIT, LicenseEnum.Apache_2_0]
    pom.sync(somesy_input.project)
    assert pom.license == ["MIT", "Apache-2.0"]


def test_save(tmp_path):
    # test save with default path
    file_path = tmp_path / "pom.xml"
    pom = POM(file_path, create_if_not_exists=True)
    pom.save()
    assert file_path.is_file()

    # test save with custom path
    custom_path = tmp_path / "custom.xml"
    pom.save(custom_path)
    assert custom_path.is_file()


def test_from_to_person(person: Person):
    p1 = POM._from_person(person)
    assert p1["name"] == person.full_name
    assert p1["email"] == person.email
    assert p1["url"] == str(person.orcid)

    p = POM._to_person(POM._from_person(person))
    assert isinstance(p, Person)
    assert p.full_name == person.full_name
    assert p.email == person.email
    assert str(p.orcid) == str(person.orcid)


def test_person_merge_without_email(tmp_path):
    pom_path = tmp_path / "pom.xml"
    person = Person(
        given_names="Jane", family_names="Doe", author=True, maintainer=True
    )
    metadata = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[person],
    )

    pom = POM(pom_path, create_if_not_exists=True)
    pom.sync(metadata)
    pom.save()

    person.maintainer = False
    pom = POM(pom_path)
    pom.sync(metadata)

    assert pom.authors[0]["name"] == person.full_name


def test_person_merge(pom_file, person: Person):
    pj = POM(pom_file)

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
    assert len(pj.maintainers) == 0
    assert pj.authors[0]["name"] == person1c.full_name
    assert pj.authors[0]["email"] == person1c.email
    print(pj.contributors)

    assert pj.contributors[0]["name"] == person2.full_name
    assert pj.contributors[0]["email"] == person2.email


def test_from_person_entity_website_is_str():
    entity = Entity(name="ACME", website="https://acme.org")
    assert POM._from_person(entity)["url"] == str(entity.website)
    assert isinstance(POM._from_person(entity)["url"], str)


def test_sync_entity_contributor_saves(tmp_path):
    pom_path = tmp_path / "pom.xml"
    metadata = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[
            Person(given_names="Jane", family_names="Doe", author=True),
            Person(given_names="John", family_names="Roe"),
        ],
        entities=[Entity(name="ACME", website="https://acme.org")],
    )
    pom = POM(pom_path, create_if_not_exists=True)
    pom.sync(metadata)
    pom.save()

    pom = POM(pom_path)
    names = [c["name"] for c in pom.contributors]
    assert sorted(names) == ["ACME", "John Roe"]


def test_to_person_single_role():
    p = POM._to_person({"name": "Jane Doe", "roles": {"role": "code"}})
    assert [c.value for c in p.contribution_types] == ["code"]


def test_authors_without_developers(tmp_path):
    pom = POM(tmp_path / "pom.xml", create_if_not_exists=True)
    assert pom.authors == []


def test_to_person_without_name(caplog):
    assert POM._to_person({"email": "a@b.com"}) is None
    assert POM._parse_people([{"email": "a@b.com"}]) == []


def test_sync_keeps_urls_if_absent(pom: POM, somesy_input):
    before = (pom.homepage, pom.repository, pom.documentation)
    project = somesy_input.project
    project.homepage = project.repository = project.documentation = None
    pom.sync(project)
    assert (pom.homepage, pom.repository, pom.documentation) == before


def test_repository_keeps_scm_connection(pom: POM, somesy_input):
    somesy_input.project.repository = "https://example.com/new/repo"
    pom.sync(somesy_input.project)
    assert pom.repository == "https://example.com/new/repo"
    scm = pom._get_property(["scm"])
    assert isinstance(scm, dict)
    assert scm["url"] == "https://example.com/new/repo"
    assert scm["connection"] == "scm:git:git@github.com:lampepfl/dotty.git"


def test_no_empty_scm_or_site_without_urls(tmp_path, somesy_input):
    project = somesy_input.project
    project.homepage = project.repository = project.documentation = None
    path = tmp_path / "pom.xml"
    pom = POM(path, create_if_not_exists=True)
    pom.sync(project)
    pom.save()
    content = path.read_text()
    assert "scm" not in content
    assert "distributionManagement" not in content
