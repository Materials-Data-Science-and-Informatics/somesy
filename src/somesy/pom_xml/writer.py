"""Writer adapter for pom.xml files."""
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

import defusedxml.ElementTree as DET

from somesy.core.models import Person
from somesy.core.writer import FieldKeyMapping, ProjectMetadataWriter

from .xmlproxy import XMLProxy

logger = logging.getLogger("somesy")

# some POM-related constants and reusable objects
POM_URL = "http://maven.apache.org/POM/4.0.0"
POM_PREF = "{" + POM_URL + "}"
POM_NS_MAP = dict(pom=POM_URL)
POM_ROOT_ATRS: Dict[str, str] = {
    "xmlns": "http://maven.apache.org/POM/4.0.0",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xsi:schemaLocation": "http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd",
}
POM_PARSER = DET.XMLParser(target=ET.TreeBuilder(insert_comments=True))

ET.register_namespace("pom", POM_URL)  # globally register xml namespace for POM

# helper methods


def new_pom() -> ET.ElementTree:
    """Create a minimal pom.xml file."""
    return ET.ElementTree(ET.Element("project", POM_ROOT_ATRS))


def parse_pom(path: Path) -> ET.ElementTree:
    """Parse a pom.xml file into an ElementTree, preserving comments."""
    return DET.parse(path, parser=POM_PARSER)


def write_pom(tree: ET.ElementTree, path: Path):
    """Write the POM DOM to a file."""
    tree.write(path, encoding="UTF-8", xml_declaration=True, default_namespace=POM_URL)


class POM(ProjectMetadataWriter):
    """Java Maven pom.xml parser and saver."""

    # TODO: write a wrapper for ElementTree that behaves like a dict
    # TODO: set up correct field name mappings

    def __init__(
        self,
        path: Path,
        create_if_not_exists: bool = True,
    ):
        """Java Maven pom.xml parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        mappings: FieldKeyMapping = None
        # {
        #     "name": ["title"],
        #     "description": ["abstract"],
        #     "homepage": ["url"],
        #     "repository": ["repository-code"],
        #     "documentation": IgnoreKey(),
        #     "maintainers": ["contact"],
        # }
        super().__init__(
            path, create_if_not_exists=create_if_not_exists, direct_mappings=mappings
        )

    def _init_new_file(self):
        """Initialize new pom.xml file."""
        write_pom(new_pom(), self.path)

    def _load(self):
        """Load the POM file."""
        self._data = XMLProxy(parse_pom(self.path))

    def _validate(self):
        """Validate the POM file."""
        logger.info("Cannot validate POM file, skipping validation.")

    def save(self, path: Optional[Path] = None) -> None:
        """Save the POM DOM to a file."""
        path = path or self.path
        write_pom(self._data, path)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to cff dict for person format."""
        raise NotImplementedError

    @staticmethod
    def _to_person(person_obj) -> Person:
        """Parse CFF Person to a somesy Person."""
        raise NotImplementedError
