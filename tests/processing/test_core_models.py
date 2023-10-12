import json

import pytest

from somesy.core.models import Person, ProjectMetadata

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


def test_detect_duplicate_person(somesy_input):
    metadata = somesy_input.project

    meta = metadata.copy()
    meta.people.append(p1)
    ProjectMetadata(**meta.dict())

    # P1 ~= P3
    meta.people.append(p3)
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.dict())

    # P1 ~= P4
    meta.people.pop()
    meta.people.append(p4)
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.dict())

    # P1 ~= P6
    meta.people.pop()
    meta.people.append(p6)
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.dict())

    # P1 /= P2
    meta.people.pop()
    meta.people.append(p2)
    ProjectMetadata(**meta.dict())

    # P1 /= P5
    meta.people.pop()
    meta.people.append(p5)
    ProjectMetadata(**meta.dict())

    # P2 ~= P5
    meta.people.append(p2)
    with pytest.raises(ValueError):
        ProjectMetadata(**meta.dict())


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
    assert list(p.dict(exclude_none=True).keys()) == expected_order
    assert list(json.loads(p.json(exclude_none=True)).keys()) == expected_order

    # added field appears in right spot
    p.orcid = "https://orcid.org/1234-5678-9101"
    assert list(p.dict(exclude_none=True).keys()) == p._key_order
    assert list(json.loads(p.json(exclude_none=True)).keys()) == p._key_order

    # fields not in key order come after all the listed ones
    p.affiliation = "Some institution"
    expected_order = p._key_order + ["affiliation"]
    assert list(p.dict(exclude_none=True).keys()) == expected_order
    assert list(json.loads(p.json(exclude_none=True)).keys()) == expected_order

    # key order also preserved by copy
    assert p.copy()._key_order == p._key_order
