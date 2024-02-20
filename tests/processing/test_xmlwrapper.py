from somesy.pom_xml import POM_URL
from somesy.pom_xml.xmlproxy import XMLProxy

import pytest


def test_parse_write(tmp_path, xml_examples):
    """Make sure that header + namespace of XML are set correctly and comments are preserved."""
    file_src = xml_examples("blank_pom.xml")
    file_trg = tmp_path / "written.xml"

    prx = XMLProxy.parse(file_src, default_namespace=POM_URL)

    # the root
    assert repr(prx).startswith(
        "<Element '{http://maven.apache.org/POM/4.0.0}project' at"
    )

    # the comment element
    assert len(prx) == 1
    lst = list(iter(prx))
    assert len(lst) == 1 and repr(lst[0]).startswith("<Element <function Comment")

    # check that namespaceing and comments are preserved
    prx.write(file_trg)
    contents = (file_trg).read_text()
    assert contents.strip() == file_src.read_text().strip()


def test_read_access(xml_examples):
    prx = XMLProxy.parse(xml_examples("example_1.xml"), default_namespace=POM_URL)

    # __iter__, __len__, __bool__, __repr__
    assert str(prx).startswith("<Element")
    assert len(prx) == 9
    assert bool(prx)
    elems = list(iter(prx))
    assert len(elems) == 9
    assert not elems[2].is_comment
    assert elems[2].tag == "listEntry"
    assert not len(elems[1])
    assert not bool(elems[1])
    assert elems[3].is_comment
    assert elems[3].tag is None

    with pytest.raises(ValueError):
        elems[3].tag = "newTag"

    el = prx["anInt"]
    el.tag = "someInt"  # change
    assert "anInt" not in prx
    assert "someInt" in prx
    el.tag = "anInt"  # restore

    # __contains__
    assert "nothing" in prx
    assert "anInt" in prx
    assert "listEntry" in prx
    assert "invalid" not in prx

    # __getitem__ / get
    with pytest.raises(KeyError):
        assert prx["invalid"]
    assert prx.get("invalid") is None
    assert len(prx.get("invalid", as_nodes=True)) == 0

    # self-closing tag and empty open/close are both an empty string
    assert prx["nothing"].tag == "nothing"
    assert prx["nothing"].to_jsonlike() == ""
    assert prx["emptyString"].to_jsonlike() == ""

    # primitive values returned as strings
    assert prx["anInt"].to_jsonlike() == "42"
    assert prx["aBool"].to_jsonlike() == "true"

    # multiple elements -> returns list
    lst = prx["listEntry"]
    assert len(lst) == 2
    assert lst[0].to_jsonlike() == "foo"
    assert lst[1].to_jsonlike() == {"someDict": {"a": "x", "b": "y"}, "someValue": "z"}

    expected = dict(
        nothing="",
        emptyString="",
        listEntry=["foo", {"someDict": {"a": "x", "b": "y"}, "someValue": "z"}],
        __comment_1__=" comment 1 ",
        aBool="true",
        __comment_2__=" comment 2 ",
        anInt="42",
        aFloat="3.14",
    )
    dct = prx.to_jsonlike()
    assert dct == expected
    assert list(dct.keys()) == list(expected.keys())  # key order correct


def test_del_set_items(xml_examples):
    prx = XMLProxy.parse(xml_examples("example_1.xml"), default_namespace=POM_URL)

    # remove existing elements
    del prx["emptyString"]
    del prx["listEntry"][1]["someDict"]["b"]

    with pytest.raises(KeyError):
        del prx["emptyString"]  # already removed
    with pytest.raises(KeyError):
        del prx["invalid"]  # not existing

    # add new elements
    prx["newValue"] = 5
    assert prx["newValue"].to_jsonlike() == "5"
    dct = dict(some="hello", keys="world")
    prx["newObject"] = dct
    assert prx["newObject"].to_jsonlike() == dct

    # overwrite existing elements
    prx["anInt"] = 123  # primitive to primitive
    assert prx["anInt"].to_jsonlike() == "123"
    prx["newValue"] = dict(x=1, y=2)  # primitive to complex
    assert prx["newValue"].to_jsonlike() == dict(x="1", y="2")
    prx["newValue"] = None  # complex to primitive
    assert prx["newValue"].to_jsonlike() == ""
    prx["listEntry"][1]["someDict"]["a"] = "qux"  # overwrite nested
    assert prx["listEntry"][1]["someDict"]["a"].to_jsonlike() == "qux"

    # overwrite specific if there are many hits
    prx[prx["listEntry"][0]] = "xyz"
    assert prx["listEntry"][0].to_jsonlike() == "xyz"
    prx[prx["listEntry"][0]] = dict(x="1", y="2")
    assert prx["listEntry"][0].to_jsonlike() == dict(x="1", y="2")
    # overwrite all elements if there are many hits
    prx["listEntry"] = 321
    assert prx["listEntry"].to_jsonlike() == "321"
    # overwrite all elements if there are many target values
    prx["listEntry"] = [123, 456]
    assert prx.get("listEntry", deep=True) == ["123", "456"]

    # elements still in right order
    exp_keys = ["nothing", None, "aBool", None, "anInt", "aFloat"]
    exp_keys += ["newValue", "newObject", "listEntry", "listEntry"]
    keys = [x.tag for x in iter(prx)]
    assert keys == exp_keys


def test_update_write(xml_examples, tmp_path):
    prx = XMLProxy.parse(xml_examples("example_pom.xml"), default_namespace=POM_URL)

    prx["version"] = "0.2.0"
    prx["licenses"]["license"] = "MIT"
    prx["developers"]["developer"][1]["name"] = "John Doe"
    prx["newKey"] = 42
    externalKey = "{https://something.com}externalKey"
    prx[externalKey] = "value"

    tmp_file = tmp_path / "written.xml"
    prx.write(tmp_file)

    # check that the comment is retained
    content = tmp_file.read_text()
    assert content.find("some comment") > 0
    # check that the changes persisted
    prs = XMLProxy.parse(tmp_file, default_namespace=POM_URL)
    assert prs["developers"]["developer"][1]["name"].to_jsonlike() == "John Doe"
    assert prs["version"].to_jsonlike() == "0.2.0"
    assert "newKey" in prs
    # check that the namespace of the external key is preserved
    assert "externalKey" not in prs
    assert externalKey in prs
