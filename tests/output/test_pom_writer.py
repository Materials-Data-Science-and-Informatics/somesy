import pytest

from somesy.pom_xml.writer import POM
from somesy.core.models import LicenseEnum, Person, ProjectMetadata


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
    assert pom.license == "MIT"
    assert len(pom.authors) == 1


def test_sync(pom: POM, somesy_input: dict):
    pom.sync(somesy_input.project)
    assert pom.name == "testproject"
    assert pom.version == "1.0.0"


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
    assert p.full_name == person.full_name
    assert p.email == person.email
    assert str(p.orcid) == str(person.orcid)


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

    assert pj.contributors[1]["name"] == person2.full_name
    assert pj.contributors[1]["email"] == person2.email

    # new person
    person3 = Person(
        **{
            "given_names": "Janice",
            "family_names": "Doethan",
            "email": "jane93@gmail.com",
            "author": True,
            "publication_author": True,
        }
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

    assert len(pj.contributors) == 3
    assert len(pj.maintainers) == 0
    assert pj.authors[0]["name"] == person1c.full_name
    assert pj.authors[0]["email"] == person1c.email
    print(pj.contributors)

    assert pj.contributors[2]["name"] == person3.full_name
    assert pj.contributors[2]["email"] == person3.email
