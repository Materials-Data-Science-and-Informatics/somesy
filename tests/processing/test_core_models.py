import json

import pytest

from somesy.core.models import (
    Entity,
    Person,
    ProjectMetadata,
    SomesyConfig,
    SomesyInput,
)

# dicts with test inputs for people
p1 = {
    "given-names": "Jane",
    "family-names": "Doe",
    "email": "j.doe@example.com",
    "orcid": "https://orcid.org/0123-4567-8910",
}
p2 = {"given-names": "Foo", "family-names": "Bar", "email": "f.bar@example.com"}
p3 = {
    "given-names": p1["given-names"],
    "family-names": p1["family-names"],
    "email": p2["email"],
}
p4 = {**p2, "email": p1["email"]}
p5 = {**p2, "orcid": "https://orcid.org/1234-5678-9101"}
p6 = {**p5, "orcid": p1["orcid"]}

# dicts with test inputs for entities
e1 = {"name": "Test Org 1"}
e2 = {"name": "Test Org 2", "email": "org2@example.com"}
e3 = {"name": "Test Org 1", "email": "org1@example.com"}
e4 = {"name": "Test Org 3", "email": "org1@example.com"}
e5 = {**e2, "rorid": "https://ror.org/12345678"}
e6 = {**e3, "rorid": "https://ror.org/87654321"}
e7 = {**e3, "rorid": e5["rorid"]}  # same rorid as e5


def test_same_person():
    # same is same (reflexivity)
    assert Person(**p1).same_person(Person(**p1))

    # missing orcid, different mail, different name -> not same
    assert not Person(**p1).same_person(Person(**p2))
    # missing orcid, different mail, same name -> same
    assert Person(**p1).same_person(Person(**p3))
    # missing orcid, same mail -> same
    assert Person(**p1).same_person(Person(**p4))
    # different orcid -> different
    assert not Person(**p1).same_person(Person(**p5))
    # same orcid -> same
    assert Person(**p1).same_person(Person(**p6))


def test_same_entity():
    # same is same (reflexivity)
    assert Entity(**e1).same_person(Entity(**e1))
    # different mail, different name -> not same
    assert not Entity(**e2).same_person(Entity(**e3))
    # same email, different name -> same
    assert Entity(**e3).same_person(Entity(**e4))
    # no email, same name -> same
    assert Entity(**e1).same_person(Entity(**e3))
    # different rorid -> different
    assert not Entity(**e5).same_person(Entity(**e6))
    # same rorid -> same
    assert Entity(**e5).same_person(Entity(**e7))


@pytest.mark.parametrize(
    ("doi", "expected"),
    [
        ("10.5281/zenodo.1234567", "10.5281/zenodo.1234567"),
        ("https://doi.org/10.5281/zenodo.1234567", "10.5281/zenodo.1234567"),
    ],
)
def test_normalize_project_doi(somesy_input, doi, expected):
    project = somesy_input.project.model_dump()
    project["doi"] = doi
    assert ProjectMetadata(**project).doi == expected


def test_reject_invalid_project_doi(somesy_input):
    project = somesy_input.project.model_dump()
    project["doi"] = "https://example.test/not-a-doi"
    with pytest.raises(ValueError, match="DOI must be"):
        ProjectMetadata(**project)


def test_detect_duplicate_person(somesy_input):
    metadata = somesy_input.project

    meta = metadata.model_copy()
    meta.people.append(Person(**p1))
    ProjectMetadata(**meta.model_dump())

    # P1 ~= P3
    meta.people.append(Person(**p3))
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.model_dump())

    # P1 ~= P4
    meta.people.pop()
    meta.people.append(Person(**p4))
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.model_dump())

    # P1 ~= P6
    meta.people.pop()
    meta.people.append(Person(**p6))
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.model_dump())

    # P1 /= P2
    meta.people.pop()
    meta.people.append(Person(**p2))
    ProjectMetadata(**meta.model_dump())

    # P1 /= P5
    meta.people.pop()
    meta.people.append(Person(**p5))
    ProjectMetadata(**meta.model_dump())

    # P2 ~= P5
    meta.people.append(Person(**p2))
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.model_dump())


def test_detect_duplicate_entity(somesy_input):
    metadata = somesy_input.project

    meta = metadata.model_copy()
    meta.entities.append(Entity(**e1))
    dump = meta.model_dump()
    ProjectMetadata(**dump)

    # E1 ~= E3
    meta.entities.append(Entity(**e3))
    with pytest.raises(ValueError):
        dump = meta.model_dump()
        ProjectMetadata(**dump)

    # E2 /= E3
    meta.entities = [Entity(**e2), Entity(**e3)]
    dump = meta.model_dump()
    ProjectMetadata(**dump)

    # E5 /= E6 (different RORIDs)
    meta.entities = [Entity(**e5), Entity(**e6)]
    dump = meta.model_dump()
    ProjectMetadata(**dump)

    # E5 ~= E7 (same RORID)
    with pytest.raises(ValueError):
        meta.entities = [Entity(**e5), Entity(**e7)]
        dump = meta.model_dump()
        ProjectMetadata(**dump)


def test_custom_key_order():
    key_order = ["given-names", "orcid", "family-names", "email"]
    p = Person(
        **{
            "given-names": "Jane",
            "email": "mail@example.com",
            "family-names": "Doe",
        }
    )
    p.set_key_order(key_order)

    # correct subsequence of order
    expected_order = ["given_names", "family_names", "email"]
    assert list(p.model_dump(exclude_none=True).keys()) == expected_order
    assert (
        list(json.loads(p.model_dump_json(exclude_none=True)).keys()) == expected_order
    )

    # added field appears in right spot
    p.orcid = "https://orcid.org/1234-5678-9101"
    assert list(p.model_dump(exclude_none=True).keys()) == p._key_order
    assert list(json.loads(p.model_dump_json(exclude_none=True)).keys()) == p._key_order

    # fields not in key order come after all the listed ones
    p.affiliation = "Some institution"
    expected_order = p._key_order + ["affiliation"]
    assert list(p.model_dump(exclude_none=True).keys()) == expected_order
    assert (
        list(json.loads(p.model_dump_json(exclude_none=True)).keys()) == expected_order
    )

    # key order also preserved by copy
    assert p.model_copy()._key_order == p._key_order


def test_orcid_from_string():
    person_dict = {
        "given-names": "Jane",
        "family-names": "Doe",
        "email": "mail@example.com",
        "orcid": "0000-0003-2637-0432",
    }
    orcid_url = "https://orcid.org/0000-0003-2637-0432"
    p = Person(**person_dict)
    assert str(p.orcid) == orcid_url

    # with http:// prefix
    person_dict["orcid"] = orcid_url
    p = Person(**person_dict)
    assert str(p.orcid) == orcid_url


def test_entity_same_name_different_identifier_is_not_same():
    """Entities with equal names but differing rorid/website are distinct."""
    a = Entity.model_validate(dict(name="Org", rorid="https://ror.org/11111111"))
    b = Entity.model_validate(dict(name="Org", rorid="https://ror.org/22222222"))
    assert not a.same_person(b)
    c = Entity.model_validate(dict(name="Org", website="https://a.example.com"))
    d = Entity.model_validate(dict(name="Org", website="https://b.example.com"))
    assert not c.same_person(d)
    # identifier only on one side: still falls back to name
    assert a.same_person(Entity(name="Org"))


def test_entity_model_dump_json():
    """rorid becomes website when none is set; unicode and key order are kept."""
    ent = Entity.model_validate(dict(name="Jülich", rorid="https://ror.org/02nv7yv05"))
    ent.set_key_order(["rorid", "name"])
    out = ent.model_dump_json()
    assert "Jülich" in out
    assert json.loads(out) == {
        "name": "Jülich",
        "website": "https://ror.org/02nv7yv05",
    }
    # rorid is kept when a website is already set
    ent = Entity.model_validate(
        dict(name="X", website="https://x.example.com", rorid="https://ror.org/1")
    )
    ent.set_key_order(["rorid", "name", "website"])
    dumped = json.loads(ent.model_dump_json())
    assert list(dumped) == ["rorid", "name", "website"]


def test_person_from_single_word_name_raises():
    """A single word is no valid person name; callers fall back to Entity."""
    with pytest.raises(ValueError, match="given-names"):
        Person.from_name_email_string("Cher <cher@x.org>")
    assert Entity.from_name_email_string("Cher <cher@x.org>").name == "Cher"


def test_somesy_input_without_input_file_is_not_somesy_file(somesy_input):
    project = somesy_input.project.model_dump()
    config = SomesyConfig(input_file=None)
    assert not SomesyInput(project=project, config=config).is_somesy_file()
