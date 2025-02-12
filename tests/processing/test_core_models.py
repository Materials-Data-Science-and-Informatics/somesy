import json

import pytest

from somesy.core.models import Person, ProjectMetadata, Entity

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
