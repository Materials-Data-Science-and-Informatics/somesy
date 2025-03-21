"""package.json parser and saver."""

import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.pretty import pretty_repr

from somesy.core.models import Entity, Person, ProjectMetadata
from somesy.core.writer import FieldKeyMapping, IgnoreKey, ProjectMetadataWriter
from somesy.json_wrapper import json
from somesy.package_json.models import PackageAuthor, PackageJsonConfig

logger = logging.getLogger("somesy")


class PackageJSON(ProjectMetadataWriter):
    """package.json parser and saver."""

    def __init__(
        self,
        path: Path,
        pass_validation: Optional[bool] = False,
    ):
        """package.json parser.

        See [somesy.core.writer.ProjectMetadataWriter.__init__][].
        """
        mappings: FieldKeyMapping = {
            "authors": ["author"],
            "documentation": IgnoreKey(),
        }
        super().__init__(
            path,
            create_if_not_exists=False,
            direct_mappings=mappings,
            pass_validation=pass_validation,
        )

    @property
    def authors(self):
        """Return the only author of the package.json file as list."""
        # check if the author has the correct format
        if isinstance(author := self._get_property(self._get_key("authors")), str):
            author = PackageJsonConfig.convert_author(author)
            if author is None:
                return []

        return [self._get_property(self._get_key("authors"))]

    @authors.setter
    def authors(self, authors: List[Union[Entity, Person]]) -> None:
        """Set the authors of the project."""
        authors_dict = self._from_person(authors[0])
        self._set_property(self._get_key("authors"), authors_dict)

    @property
    def maintainers(self):
        """Return the maintainers of the package.json file."""
        # check if the maintainer has the correct format
        maintainers = self._get_property(self._get_key("maintainers"))
        # return empty list if maintainers is None
        if maintainers is None:
            return []

        maintainers_valid = []

        for maintainer in maintainers:
            if isinstance(maintainer, str):
                maintainer = PackageJsonConfig.convert_author(maintainer)
                if maintainer is None:
                    continue
            maintainers_valid.append(maintainer)
        return maintainers_valid

    @maintainers.setter
    def maintainers(self, maintainers: List[Union[Entity, Person]]) -> None:
        """Set the maintainers of the project."""
        maintainers_dict = [self._from_person(m) for m in maintainers]
        self._set_property(self._get_key("maintainers"), maintainers_dict)

    @property
    def contributors(self):
        """Return the contributors of the package.json file."""
        # check if the contributor has the correct format
        contributors = self._get_property(self._get_key("contributors"))
        # return empty list if contributors is None
        if contributors is None:
            return []

        contributors_valid = []

        for contributor in contributors:
            if isinstance(contributor, str):
                contributor = PackageJsonConfig.convert_author(contributor)
                if contributor is None:
                    continue
            contributors_valid.append(contributor)
        return contributors_valid

    @contributors.setter
    def contributors(self, contributors: List[Union[Entity, Person]]) -> None:
        """Set the contributors of the project."""
        contributors_dict = [self._from_person(c) for c in contributors]
        self._set_property(self._get_key("contributors"), contributors_dict)

    def _load(self) -> None:
        """Load package.json file."""
        with self.path.open() as f:
            self._data = json.load(f, object_pairs_hook=OrderedDict)

    def _validate(self) -> None:
        """Validate package.json content using pydantic class."""
        if self.pass_validation:
            return
        config = dict(self._get_property([]))
        logger.debug(
            f"Validating config using {PackageJsonConfig.__name__}: {pretty_repr(config)}"
        )
        PackageJsonConfig(**config)

    def save(self, path: Optional[Path] = None) -> None:
        """Save the package.json file."""
        path = path or self.path
        logger.debug(f"Saving package.json to {path}")

        with path.open("w") as f:
            # package.json indentation is 2 spaces
            json.dump(self._data, f)

    @staticmethod
    def _from_person(person: Union[Entity, Person]) -> dict:
        """Convert project metadata person/entity object to package.json dict for person format."""
        response = {}
        if isinstance(person, Person):
            response["name"] = person.full_name
            if person.orcid:
                response["url"] = str(person.orcid)
        else:
            response["name"] = person.name
            if person.website:
                response["url"] = person.website

        if person.email:
            response["email"] = person.email

        return response

    @staticmethod
    def _to_person(
        person: Union[str, Dict[str, Any], PackageAuthor],
    ) -> Union[Entity, Person]:
        """Convert package.json dict or str for person format to project metadata person object."""
        if isinstance(person, str):
            # parse from package.json format
            person = PackageJsonConfig.convert_author(person)

        if isinstance(person, PackageAuthor):
            person = person.model_dump(exclude_none=True)

        person_dict: dict[str, Any] = person  # type: ignore

        if "name" in person_dict and " " in person_dict["name"]:
            names = list(map(lambda s: s.strip(), person_dict["name"].split()))
            person_obj = {
                "given-names": " ".join(names[:-1]),
                "family-names": names[-1],
            }
            if "email" in person_dict:
                person_obj["email"] = person_dict["email"].strip()
            if "url" in person_dict:
                person_obj["orcid"] = person_dict["url"].strip()
            return Person(**person_obj)
        else:
            entity_obj = {"name": person_dict["name"]}
            if "email" in person_dict:
                entity_obj["email"] = person_dict["email"].strip()
            if "url" in person_dict:
                entity_obj["orcid"] = person_dict["url"].strip()
            return Entity(**entity_obj)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync package.json with project metadata.

        Use existing sync function from ProjectMetadataWriter but update repository and contributors.
        """
        super().sync(metadata)
        self.contributors = self._sync_person_list(self.contributors, metadata.people)

    @property
    def repository(self) -> Optional[Union[str, Dict]]:
        """Return the repository url of the project."""
        if repo := super().repository:
            if isinstance(repo, str):
                return repo
            else:
                return repo.get("url")
        else:
            return None

    @repository.setter
    def repository(self, value: Optional[Union[str, Dict]]) -> None:
        """Set the repository url of the project."""
        if value is None:
            self._set_property(self._get_key("repository"), None)
        else:
            self._set_property(self._get_key("repository"), dict(type="git", url=value))
