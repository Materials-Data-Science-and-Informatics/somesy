"""Writer adapter for pom.xml files."""
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from somesy.core.models import Person
from somesy.core.writer import FieldKeyMapping, ProjectMetadataWriter

from . import POM_ROOT_ATRS, POM_URL
from .xmlproxy import XMLProxy

ET.register_namespace("pom", POM_URL)  # globally register xml namespace for POM
logger = logging.getLogger("somesy")


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
        mappings: FieldKeyMapping = {
            "year": ["inceptionYear"],
            "license": ["licenses", "license"],
            "homepage": ["url"],
            "project_slug": ["artifactId"],
            "authors": ["developers", "developer"],
            "contributors": ["contributors", "contributor"],
        }
        super().__init__(
            path, create_if_not_exists=create_if_not_exists, direct_mappings=mappings
        )

    def _init_new_file(self):
        """Initialize new pom.xml file."""
        pom = XMLProxy(ET.Element("project", POM_ROOT_ATRS))
        pom["properties"] = {"info.versionScheme": "semver-spec"}
        pom.write(self.path, default_namespace=POM_URL)

    def _load(self):
        """Load the POM file."""
        self._data = XMLProxy.parse(self.path, default_namespace=POM_URL)

    def _validate(self):
        """Validate the POM file."""
        logger.info("Cannot validate POM file, skipping validation.")

    def save(self, path: Optional[Path] = None) -> None:
        """Save the POM DOM to a file."""
        path = path or self.path
        self._data.write(path)

    @staticmethod
    def _from_person(person: Person):
        """Convert project metadata person object to cff dict for person format."""
        ret = {}
        person_id = person.orcid or person.to_name_email_string()
        ret["id"] = person_id
        ret["name"] = person.name
        ret["email"] = person.email
        if person.orcid:
            ret["url"] = person.orcid
        if person.contribution_types:
            ret["roles"] = dict(role=person.contribution_types)
        return ret

    @staticmethod
    def _to_person(person_obj) -> Person:
        """Parse CFF Person to a somesy Person."""
        return Person(
            name=person_obj["name"],
            email=person_obj["email"],
            orcid=person_obj["orcid"],
            contribution_types=person_obj["roles"]["role"],
        )
        raise NotImplementedError
