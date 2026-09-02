"""Writer adapter for pom.xml files."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from somesy.core.models import Entity, Person
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
        pass_validation: bool | None = False,
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
            path,
            create_if_not_exists=create_if_not_exists,
            direct_mappings=mappings,
            pass_validation=pass_validation,
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

    def _validate(self) -> None:
        """Validate the POM file."""
        logger.info("Cannot validate POM file, skipping validation.")

    def save(self, path: Path | None = None) -> None:
        """Save the POM DOM to a file."""
        self._data.write(path or self.path, default_namespace=None)

    def _get_property(
        self,
        key: str | list[str],
        *,
        only_first: bool = False,
        remove: bool = False,
    ) -> Any | None:
        """Get (a) property by key."""
        elem = super()._get_property(key, only_first=only_first, remove=remove)
        if elem is not None:
            if isinstance(elem, list):
                return [e.to_jsonlike() for e in elem]
            else:
                return elem.to_jsonlike()
        return None

    @staticmethod
    def _from_person(person: Entity | Person):
        """Convert person object to dict for POM XML person format."""
        ret: dict[str, Any] = {}
        if isinstance(person, Person):
            person_id = person.to_name_email_string()
            if person.orcid:
                person_id = str(person.orcid)
                ret["url"] = str(person.orcid)
        else:
            person_id = person.to_name_email_string()
            if person.website:
                person_id = str(person.website)
                ret["url"] = person.website
        ret["id"] = person_id
        ret["name"] = person.full_name
        if person.email:
            ret["email"] = person.email
        if person.contribution_types:
            ret["roles"] = {"role": [c.value for c in person.contribution_types]}
        return ret

    @staticmethod
    def _to_person(person_obj: dict) -> Entity | Person:
        """Parse POM XML person to a somesy Person."""
        if " " in person_obj["name"]:
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
        else:
            name = person_obj["name"]
            email = person_obj.get("email")
            url = person_obj.get("url")
            if roles := person_obj.get("roles"):
                contr = roles["role"]
            else:
                contr = None

            return Entity(
                name=name,
                email=email,
                website=url,
                contribution_types=contr,
            )

    # no search keywords supported in POM
    @property
    def keywords(self) -> list[str] | None:
        """Return the keywords of the project."""

    @keywords.setter
    def keywords(self, keywords: list[str]) -> None:
        """Set the keywords of the project."""

    # authors must be a list
    @property
    def authors(self):
        """Return the authors of the project."""
        authors = self._get_property(self._get_key("authors"))
        return authors if isinstance(authors, list) else [authors]

    @authors.setter
    def authors(self, authors: list[Entity | Person]) -> None:
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
    def contributors(self, contributors: list[Entity | Person]) -> None:
        """Set the contributors of the project."""
        contr = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contr)

    # no maintainers supported im POM, only developers and contributors
    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        return []

    @maintainers.setter
    def maintainers(self, maintainers: list[Person]) -> None:
        """Set the maintainers of the project."""

    @property
    def license(self) -> str | list[str] | None:
        """Return the license of the project."""
        licenses = self._get_property(self._get_key("license"))
        if licenses is None:
            return None
        licenses = licenses if isinstance(licenses, list) else [licenses]
        names = [license["name"] for license in licenses]
        return names[0] if len(names) == 1 else names

    @license.setter
    def license(self, license: str | list[str] | None) -> None:
        """Set the license of the project."""
        licenses = license if isinstance(license, list) else [license]
        self._set_property(
            self._get_key("license"),
            [{"name": license, "distribution": "repo"} for license in licenses],
        )

    @property
    def repository(self) -> str | dict | None:
        """Return the repository url of the project."""
        repo = super().repository
        if isinstance(repo, str):
            return repo
        return repo.get("url") if repo is not None else None

    @repository.setter
    def repository(self, value: str | dict | None) -> None:
        """Set the repository url of the project."""
        self._set_property(
            self._get_key("repository"), {"name": "git repository", "url": value}
        )

    @property
    def documentation(self) -> str | dict | None:
        """Return the documentation url of the project."""
        docs = super().documentation
        if isinstance(docs, str):
            return docs
        return docs.get("url") if docs is not None else None

    @documentation.setter
    def documentation(self, value: str | dict | None) -> None:
        """Set the documentation url of the project."""
        self._set_property(
            self._get_key("documentation"), {"name": "documentation site", "url": value}
        )

    def sync(self, metadata) -> None:
        """Sync codemeta.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        super().sync(metadata)
        licenses = metadata.license
        self.license = (
            [license.value for license in licenses]
            if isinstance(licenses, list)
            else licenses.value
        )
        self.contributors = self._sync_person_list(self.contributors, metadata.people)
