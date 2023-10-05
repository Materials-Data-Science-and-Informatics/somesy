import pytest

from somesy.cff.writer import CFF
from somesy.core.models import LicenseEnum, Person, ProjectMetadata


@pytest.fixture
def cff(load_files, file_types):
    files = load_files([file_types.CITATION])
    return files[file_types.CITATION]


def test_content_match(cff: CFF):
    assert cff.name == "test-package"
    assert cff.description == "This is a test package for demonstration purposes."
    assert cff.license == "MIT"
    assert len(cff.authors) == 1


def test_sync(cff: CFF, somesy_input: dict):
    cff.sync(somesy_input.project)
    assert cff.name == "testproject"
    assert cff.version == "1.0.0"


def test_save(tmp_path):
    # test save with default path
    file_path = tmp_path / "CITATION.cff"
    cff = CFF(file_path, create_if_not_exists=True)
    cff.save()
    assert file_path.is_file()

    # test save with custom path
    custom_path = tmp_path / "custom.cff"
    cff.save(custom_path)
    assert custom_path.is_file()


def test_from_to_person(person: Person):
    assert CFF._from_person(person) == person.model_dump(by_alias=True)

    p = CFF._to_person(CFF._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email
    assert p.orcid == str(person.orcid)


def test_person_merge(tmp_path, person: Person):
    def to_cff_keys(lst):
        return list(map(lambda s: s.replace("_", "-"), lst))

    cff_path = tmp_path / "CITATION.cff"
    cff = CFF(cff_path, create_if_not_exists=True)

    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        version="0.1.0",
        people=[person.model_copy(update=dict(author=True, publication_author=True))],
    )
    cff.sync(pm)
    cff.save()

    # check that serialization preserves key order
    # (load raw dict from yaml and see order of keys)
    dct = cff._yaml.load(open(cff_path))
    assert list(dct["authors"][0].keys()) == to_cff_keys(person._key_order)

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
    print("people:", pm.people, sep="\n")
    cff.sync(pm)
    cff.save()

    # existing author order preserved
    assert cff.authors[0] == person1b.model_dump(
        by_alias=True, exclude={"author", "publication_author"}
    )
    assert cff.authors[1] == person2.model_dump(
        by_alias=True, exclude={"author", "publication_author"}
    )
    # existing author field order preserved
    dct = cff._yaml.load(open(cff_path, "r"))
    assert list(dct["authors"][0].keys()) == to_cff_keys(person1b._key_order)
    assert list(dct["authors"][1].keys()) == to_cff_keys(person2._key_order)

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
    cff.sync(pm)
    cff.save()

    assert len(cff.authors) == 2
    assert len(cff.maintainers) == 1
    assert cff.authors[0] == person1c.model_dump(
        by_alias=True, exclude={"author", "publication_author"}
    )
    assert cff.authors[1] == person3.model_dump(
        by_alias=True, exclude={"author", "publication_author"}
    )
    dct = cff._yaml.load(open(cff_path, "r"))
    assert list(dct["authors"][0].keys()) == to_cff_keys(person1c._key_order)
