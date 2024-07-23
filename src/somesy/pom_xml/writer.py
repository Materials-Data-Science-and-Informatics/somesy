"""Writer adapter for pom.xml files."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from somesy.core.models import Person
from somesy.core.writer import FieldKeyMapping, ProjectMetadataWriter

from . import POM_ROOT_ATRS, POM_URL
from .xmlproxy import XMLProxy

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
            # "year": ["inceptionYear"],  # not supported by somesy + does not really change
            # "project_slug": ["artifactId"],  # not supported by somesy for sync
            "license": ["licenses", "license"],
            "homepage": ["url"],
            "repository": ["scm"],
            "documentation": ["distributionManagement", "site"],
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
        pom.write(self.path)

    def _load(self):
        """Load the POM file."""
        ET.register_namespace("", POM_URL)  # register POM as default xml namespace
        self._data = XMLProxy.parse(self.path, default_namespace=POM_URL)

    def _validate(self):
        """Validate the POM file."""
        logger.info("Cannot validate POM file, skipping validation.")

    def save(self, path: Optional[Path] = None) -> None:
        """Save the POM DOM to a file."""
        self._data.write(path or self.path, default_namespace=None)

    def _get_property(
        self,
        key: Union[str, List[str]],
        *,
        only_first: bool = False,
        remove: bool = False,
    ) -> Optional[Any]:
        elem = super()._get_property(key, only_first=only_first, remove=remove)
        if elem is not None:
            if isinstance(elem, list):
                return [e.to_jsonlike() for e in elem]
            else:
                return elem.to_jsonlike()
        return None

    @staticmethod
    def _from_person(person: Person):
        """Convert person object to dict for POM XML person format."""
        ret: Dict[str, Any] = {}
        person_id = str(person.orcid) or person.to_name_email_string()
        ret["id"] = person_id
        ret["name"] = person.full_name
        ret["email"] = person.email
        if person.orcid:
            ret["url"] = str(person.orcid)
        if person.contribution_types:
            ret["roles"] = dict(role=[c.value for c in person.contribution_types])
        return ret

    @staticmethod
    def _to_person(person_obj) -> Person:
        """Parse POM XML person to a somesy Person."""
        print(person_obj)
        names = person_obj["name"].split()
        gnames = " ".join(names[:-1])
        fname = names[-1]
        email = person_obj["email"]
        url = person_obj.get("url")
        maybe_orcid = url if url.find("orcid.org") >= 0 else None
        if roles := person_obj.get("roles"):
            contr = roles["role"]
        else:
            contr = None

        return Person(
            given_names=gnames,
            family_names=fname,
            email=email,
            orcid=maybe_orcid,
            contribution_types=contr,
        )

    # no search keywords supported in POM
    @property
    def keywords(self) -> Optional[List[str]]:
        """Return the keywords of the project."""
        pass

    @keywords.setter
    def keywords(self, keywords: List[str]) -> None:
        """Set the keywords of the project."""
        pass

    # authors must be a list
    @property
    def authors(self):
        """Return the authors of the project."""
        authors = self._get_property(self._get_key("authors"))
        return authors if isinstance(authors, list) else [authors]

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set the authors of the project."""
        authors = [self._from_person(c) for c in authors]
        self._set_property(self._get_key("authors"), authors)

    # contributors must be a list
    @property
    def contributors(self):
        """Return the contributors of the project."""
        contr = self._get_property(self._get_key("contributors"))
        if contr is None:
            return []
        return contr if isinstance(contr, list) else [contr]

    @contributors.setter
    def contributors(self, contributors: List[Person]) -> None:
        """Set the contributors of the project."""
        contr = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contr)

    # no maintainers supported im POM, only developers and contributors
    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        return []

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set the maintainers of the project."""
        pass

    # only one project license supported in somesy (POM can have many)
    @property
    def license(self) -> Optional[str]:
        """Return the license of the project."""
        lic = self._get_property(self._get_key("license"), only_first=True)
        return lic.get("name") if lic is not None else None

    @license.setter
    def license(self, license: Optional[str]) -> None:
        """Set the license of the project."""
        self._set_property(
            self._get_key("license"), dict(name=license, distribution="repo")
        )

    @property
    def repository(self) -> Optional[Union[str, dict]]:
        """Return the repository url of the project."""
        repo = super().repository
        if isinstance(repo, str):
            return repo
        return repo.get("url") if repo is not None else None

    @repository.setter
    def repository(self, value: Optional[Union[str, dict]]) -> None:
        """Set the repository url of the project."""
        self._set_property(
            self._get_key("repository"), dict(name="git repository", url=value)
        )

    @property
    def documentation(self) -> Optional[Union[str, dict]]:
        """Return the documentation url of the project."""
        docs = super().documentation
        if isinstance(docs, str):
            return docs
        return docs.get("url") if docs is not None else None

    @documentation.setter
    def documentation(self, value: Optional[Union[str, dict]]) -> None:
        """Set the documentation url of the project."""
        self._set_property(
            self._get_key("documentation"), dict(name="documentation site", url=value)
        )

    def sync(self, metadata) -> None:
        """Sync codemeta.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        super().sync(metadata)
        self.contributors = self._sync_person_list(self.contributors, metadata.people)
