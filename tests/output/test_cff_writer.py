from pathlib import Path

import pytest

from somesy.cff.writer import CFF
from somesy.core.models import LicenseEnum, Person, ProjectMetadata


def test_load(create_files, file_types):
    tmp_path = create_files([{file_types.CITATION: "CITATION.cff"}])
    not_exist_path = Path("reject/CITATION.cff")
    with pytest.raises(FileNotFoundError):
        CFF(not_exist_path, create_if_not_exists=False)

    file_path = tmp_path / "CITATION.cff"
    CFF(file_path, create_if_not_exists=False)
    assert file_path.is_file()


def test_content_match(load_files, file_types):
    files = load_files([file_types.CITATION])
    cff = files[file_types.CITATION]
    assert cff.name == "test-package"
    assert cff.description == "This is a test package for demonstration purposes."
    assert cff.license == "MIT"
    assert len(cff.authors) == 1


def test_sync(cff, somesy_input):
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


@pytest.fixture
def person():
    p = {
        "given-names": "Jane",
        "email": "j.doe@example.com",
        "family-names": "Doe",
        "orcid": "https://orcid.org/0123-4567-8910",
    }
    ret = Person(**p)
    ret.set_key_order(list(p.keys()))  # custom order!
    return ret


def test_from_to_person(person):
    assert CFF._from_person(person) == person.dict(by_alias=True)

    p = CFF._to_person(CFF._from_person(person))
    assert p.full_name == person.full_name
    assert p.email == person.email
    assert p.orcid == person.orcid


def test_person_merge(tmp_path, person):
    def to_cff_keys(lst):
        return list(map(lambda s: s.replace("_", "-"), lst))

    cff_path = tmp_path / "CITATION.cff"
    cff = CFF(cff_path, create_if_not_exists=True)

    pm = ProjectMetadata(
        name="My awesome project",
        description="Project description",
        license=LicenseEnum.MIT,
        people=[person.copy(update=dict(author=True))],
    )
    cff.sync(pm)
    cff.save()

    # check that serialization preserves key order
    # (load raw dict from yaml and see order of keys)
    dct = cff._yaml.load(open(cff_path))
    assert list(dct["authors"][0].keys()) == to_cff_keys(person._key_order)

    # jane becomes john -> modified person
    person1b = person.copy(update={"given_names": "John", "author": True})

    # different Jane Doe with different orcid -> new person
    person2 = person.copy(
        update={
            "orcid": "https://orcid.org/4321-0987-3231",
            "email": "i.am.jane@doe.com",
            "author": True,
        }
    )
    # use different order, just for some difference
    person2.set_key_order(["given_names", "orcid", "family_names", "email"])

    # listed in "arbitrary" order in somesy metadata (new person comes first)
    pm.people = [person2, person1b]  # need to assign like that to keep _key_order
    cff.sync(pm)
    cff.save()

    # existing author order preserved
    assert cff.authors[0] == person1b.dict(by_alias=True, exclude={"author"})
    assert cff.authors[1] == person2.dict(by_alias=True, exclude={"author"})
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
        }
    )
    # john has a new email address
    person1c = person1b.copy(update={"email": "john.of.us@qualityland.com"})
    # jane 2 is removed from authors, but added to maintainers
    person2.author = False
    person2.maintainer = True
    # reflect in project metadata
    pm.people = [person3, person2, person1c]
    # sync to CFF file
    cff.sync(pm)
    cff.save()

    assert len(cff.authors) == 2
    assert len(cff.maintainers) == 1
    assert cff.authors[0] == person1c.dict(by_alias=True, exclude={"author"})
    assert cff.authors[1] == person3.dict(by_alias=True, exclude={"author"})
    dct = cff._yaml.load(open(cff_path, "r"))
    assert list(dct["authors"][0].keys()) == to_cff_keys(person1c._key_order)
