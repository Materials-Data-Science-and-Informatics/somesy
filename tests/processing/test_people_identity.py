"""Tests for person identity matching and person syncing."""

import logging

import pytest

from somesy.cff.writer import CFF
from somesy.core.models import LicenseEnum, Person, ProjectMetadata
from somesy.merge import merge_metadata

ORCID1 = "https://orcid.org/0000-0002-1825-0097"
ORCID2 = "https://orcid.org/0000-0001-5109-3700"


def _person(orcid=None, **kwargs):
    return Person(
        given_names="Jane",
        family_names="Doe",
        orcid=orcid,
        author=True,
        publication_author=True,
        **kwargs,
    )


def _meta(*people):
    return ProjectMetadata(
        name="p", description="d", license=LicenseEnum.MIT, people=list(people)
    )


def _cff(tmp_path, authors):
    cff = CFF(tmp_path / "CITATION.cff", create_if_not_exists=True)
    cff._data["authors"] = authors
    return cff


# A1
@pytest.mark.parametrize(
    "field,value,key",
    [
        ("orcid", ORCID1, "orcid"),
        ("email", "j@x.org", "email"),
        ("affiliation", "Uni", "affiliation"),
    ],
)
def test_sync_removes_field_missing_from_input(tmp_path, field, value, key):
    cff = _cff(
        tmp_path,
        [{"family-names": "Doe", "given-names": "Jane", key: value}],
    )
    cff.sync(_meta(_person()))
    assert key not in cff._data["authors"][0]


# A2
def test_pqr_does_not_raise_and_distinct_orcids_stay_distinct():
    p, q, r = _person(ORCID1), _person(), _person(ORCID2)
    assert not p.same_person(r)
    meta = _meta(p, q, r)
    assert len(meta.people) == 3


def test_pqr_true_duplicates_still_raise():
    with pytest.raises(ValueError, match="twice"):
        _meta(_person(ORCID1), _person())


def test_merge_ambiguous_match_prefers_orcid_and_warns(caplog):
    src = {"people": [_person(ORCID1), _person(ORCID2)]}
    incoming = {"people": [_person(ORCID2, email="j@x.org")]}
    with caplog.at_level(logging.WARNING, logger="somesy"):
        merged = merge_metadata([src, incoming], allow_incomplete=True)
    by_orcid = {str(p.orcid): p for p in merged.people}
    assert by_orcid[ORCID2].email == "j@x.org"
    assert by_orcid[ORCID1].email is None


def test_merge_ambiguous_match_warns(caplog):
    src = {"people": [_person(ORCID1), _person(ORCID2)]}
    incoming = {"people": [_person(email="j@x.org")]}
    with caplog.at_level(logging.WARNING, logger="somesy"):
        merged = merge_metadata([src, incoming], allow_incomplete=True)
    assert "Jane Doe" in caplog.text
    assert [p.email for p in merged.people] == ["j@x.org", None]


def test_writer_updates_single_match_only(tmp_path, caplog):
    cff = _cff(
        tmp_path,
        [
            {"family-names": "Doe", "given-names": "Jane", "orcid": ORCID1},
            {"family-names": "Doe", "given-names": "Jane", "orcid": ORCID2},
        ],
    )
    with caplog.at_level(logging.WARNING, logger="somesy"):
        cff.sync(_meta(_person(email="j@x.org")))
    emails = [a.get("email") for a in cff._data["authors"]]
    assert emails.count("j@x.org") == 1
    assert "Jane Doe" in caplog.text


# A3
def test_sync_keeps_unparseable_entries(tmp_path, monkeypatch):
    weird = {"family-names": "Weird", "given-names": "Entry", "x": 1}
    cff = _cff(tmp_path, [weird, {"family-names": "Doe", "given-names": "Jane"}])
    orig = CFF._to_person

    def to_person(obj):
        return None if obj.get("family-names") == "Weird" else orig(obj)

    monkeypatch.setattr(CFF, "_to_person", staticmethod(to_person))
    cff.sync(_meta(_person()))
    assert weird in cff._data["authors"]
    assert len(cff._data["authors"]) == 2


# A3 follow-up: subclass setters only get Person/Entity, raw entries re-attached
def test_pom_sync_keeps_unparseable_entry_without_crash(tmp_path):
    from somesy.pom_xml.writer import POM

    pom = POM(tmp_path / "pom.xml", create_if_not_exists=True)
    weird = {"email": "nameless@x.org"}  # no name -> unparseable
    pom._set_property(
        pom._get_key("authors"), [weird, {"name": "Jane Doe", "email": "a@b.org"}]
    )
    pom.sync(_meta(_person()))
    authors = pom._get_property(pom._get_key("authors"))
    assert weird in authors
    assert len(authors) == 2


def test_codemeta_sync_with_unparseable_entry_does_not_crash(tmp_path, monkeypatch):
    from somesy.codemeta import CodeMeta

    cm = CodeMeta(tmp_path / "codemeta.json", merge=True)
    weird = {"@type": "Person", "familyName": "Weird"}
    cm._set_property(cm._get_key("authors"), [weird])
    orig = CodeMeta._to_person
    monkeypatch.setattr(
        CodeMeta,
        "_to_person",
        staticmethod(lambda o: None if o.get("familyName") == "Weird" else orig(o)),
    )
    cm.sync(_meta(_person()))  # codemeta resets its person lists by design
    assert cm._get_property(cm._get_key("authors"))[0]["familyName"] == "Doe"


def test_single_slot_author_still_works(tmp_path):
    from somesy.package_json.writer import PackageJSON

    path = tmp_path / "package.json"
    path.write_text('{"name": "x", "version": "1.0.0", "author": "Foo Bar"}')
    pj = PackageJSON(path)
    pj.sync(_meta(_person()))
    pj.save()
