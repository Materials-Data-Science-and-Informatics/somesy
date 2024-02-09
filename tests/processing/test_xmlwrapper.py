from somesy.pom_xml import POM_URL
from somesy.pom_xml.xmlproxy import XMLProxy

EMPTY_POM = """<?xml version='1.0' encoding='UTF-8'?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
<!-- contents of POM file -->
</project>"""


def test_parse_write(tmp_path):
    """Make sure that header + namespace of XML are set correctly and comments are preserved."""
    file_src = tmp_path / "blank_pom.xml"
    file_trg = tmp_path / "written.xml"

    # write a blank test pom.xml file
    with open(file_src, "w") as f:
        f.write(EMPTY_POM)

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
    assert contents == EMPTY_POM
