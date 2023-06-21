"""Core models for the somesy package."""
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyUrl, BaseModel, Extra, Field, root_validator
from typing_extensions import Annotated

from .types import ContributionTypeEnum, Country, LicenseEnum

# --------
# Somesy configuration model


TARGETS = ["cff", "pyproject", "codemeta"]


class SomesyConfig(BaseModel):
    """Pydantic model for somesy configuration.

    All fields that are not explicitly passed are initialized with default values.
    """

    class Config:
        """Pydantic model config."""

        extra = "forbid"

    @root_validator
    def at_least_one_target(cls, values):
        """Check that at least one output file is enabled."""
        if all(map(lambda x: values.get(f"no_sync_{x}"), TARGETS)):
            msg = "No sync target enabled, nothing to do. Probably this is a mistake?"
            raise ValueError(msg)

        return values

    input_file: Path = Field(
        Path(".somesy.toml"), description="Project metadata input file path."
    )

    no_sync_cff: bool = Field(False, description="Do not sync with CFF.")
    cff_file: Path = Field(Path("CITATION.cff"), description="CFF file path.")
    no_sync_pyproject: bool = Field(
        False, description="Do not sync with pyproject.toml."
    )
    pyproject_file: Path = Field(
        Path("pyproject.toml"), description="pyproject.toml file path."
    )
    no_sync_codemeta: bool = Field(False, description="Do not sync with codemeta.json.")
    codemeta_file: Path = Field(
        Path("codemeta.json"), description="codemeta.json file path."
    )
    show_info: bool = Field(
        False, description="Show basic information messages on run."
    )
    verbose: bool = Field(False, description="Show verbose messages on run.")
    debug: bool = Field(False, description="Show debug messages on run.")


# --------
# Project metadata model (modified from CITATION.cff)


class Person(BaseModel):
    """A person that is used in project metadata. Required fields are given-names, family-names, and  email."""

    class Config:
        """Configuration for the Person model."""

        extra = Extra.forbid

    address: Optional[
        Annotated[str, Field(min_length=1, description="The person's address.")]
    ]
    affiliation: Optional[
        Annotated[str, Field(min_length=1, description="The person's affiliation.")]
    ]
    alias: Optional[
        Annotated[str, Field(min_length=1, description="The person's alias.")]
    ]
    city: Optional[
        Annotated[str, Field(min_length=1, description="The person's city.")]
    ]
    country: Optional[Country] = Field(None, description="The person's country.")
    email: Annotated[
        str,
        Field(
            regex=r"^[\S]+@[\S]+\.[\S]{2,}$",
            description="The person's email address.",
        ),
    ]
    family_names: Annotated[
        str,
        Field(
            min_length=1,
            alias="family-names",
            description="The person's family names.",
        ),
    ]
    fax: Optional[
        Annotated[str, Field(min_length=1, description="The person's fax number.")]
    ]
    given_names: Annotated[
        str,
        Field(
            min_length=1,
            alias="given-names",
            description="The person's given names.",
        ),
    ]
    name_particle: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                alias="name-particle",
                description="The person's name particle, e.g., a nobiliary particle or a preposition meaning 'of' or 'from' (for example 'von' in 'Alexander von Humboldt').",
                examples=["von"],
            ),
        ]
    ]
    name_suffix: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                alias="name-suffix",
                description="The person's name-suffix, e.g. 'Jr.' for Sammy Davis Jr. or 'III' for Frank Edwin Wright III.",
                examples=["Jr.", "III"],
            ),
        ]
    ]
    orcid: Optional[AnyUrl] = Field(None, description="The person's ORCID url.")
    post_code: Optional[
        Annotated[
            str,
            Field(
                min_length=1, alias="post-code", description="The person's post-code."
            ),
        ]
    ]
    region: Optional[
        Annotated[str, Field(min_length=1, description="The person's region.")]
    ]
    tel: Optional[
        Annotated[str, Field(min_length=1, description="The person's phone number.")]
    ]
    website: Optional[AnyUrl] = Field(None, description="The person's website.")
    contribution: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                description="Summary of how the person contributed to the project.",
            ),
        ]
    ]
    contribution_type: Optional[
        Union[ContributionTypeEnum, List[ContributionTypeEnum]]
    ] = Field(None, description="Contribution type of contributor.")
    contribution_begin: Optional[date] = Field(
        None, description="Beginning date of the contribution."
    )
    contribution_end: Optional[date] = Field(
        None, description="Ending date of the contribution."
    )

    @property
    def full_name(self) -> str:
        """Return the full name of the person."""
        names = []

        if self.given_names:
            names.append(self.given_names)

        if self.name_particle:
            names.append(self.name_particle)

        if self.family_names:
            names.append(self.family_names)

        if self.name_suffix:
            names.append(self.name_suffix)

        if not names:
            return ""
        return " ".join(names)


class ProjectMetadata(BaseModel):
    """Pydantic model for Project Metadata Input."""

    name: Annotated[str, Field(min_length=2, description="Package name.")]
    description: Annotated[str, Field(min_length=1, description="Package description.")]
    version: Optional[
        Annotated[str, Field(min_length=1, description="Package version.")]
    ]
    authors: List[Person] = Field(None, description="Package authors.")
    maintainers: Optional[List[Person]] = Field(
        None, description="Package maintainers."
    )
    contributors: Optional[List[Person]] = Field(
        None, description="Package contributors."
    )
    keywords: Optional[List[str]] = Field(
        None, description="Keywords that describe the package."
    )
    license: LicenseEnum = Field(None, description="SPDX License string.")
    repository: Optional[AnyUrl] = Field(None, description="URL of the repository.")
    homepage: Optional[AnyUrl] = Field(None, description="URL of the package homepage.")


class ProjectMetadataWriter(ABC):
    """Base class for Project Metadata Output Wrapper.

    All supported output formats are implemented as subclasses.
    """

    def __init__(
        self,
        path: Path,
        *,
        create_if_not_exists: Optional[bool] = False,
        direct_mappings: Dict[str, List[str]] = None,
    ) -> None:
        """Initialize the Project Metadata Output Wrapper.

        Use the `direct_mappings` dict to define
        format-specific location for certain fields,
        if no additional processing is needed that
        requires a customized setter.

        Args:
            path: Path to target output file.
            create_if_not_exists: Create an empty CFF file if not exists. Defaults to True.
            direct_mappings: Dict with direct mappings of keys between somesy and target
        """
        self._data: Dict = {}
        self.path = path
        self.create_if_not_exists = create_if_not_exists
        self.direct_mappings = direct_mappings or {}

        if self.path.is_file():
            self._load()
            self._validate()
        else:
            if self.create_if_not_exists:
                self._init_new_file()
            else:
                raise FileNotFoundError(f"The file {self.path} does not exist.")

    def _init_new_file(self) -> None:
        """Create an new suitable target file.

        Override to initialize file with minimal contents, if needed.
        Make sure to set `self._data` to match the contents.
        """
        self.path.touch()

    @abstractmethod
    def _load(self):
        """Load the output file and validate it.

        Implement this method so that it loads the file `self.path`
        into the `self._data` dict.

        The file is guaranteed to exist.
        """

    @abstractmethod
    def _validate(self):
        """Validate the target file data.

        Implement this method so that it checks
        the validity of the metadata (relevant to somesy)
        in that file and raises exceptions on failure.
        """

    @abstractmethod
    def save(self, path: Optional[Path]) -> None:
        """Save the output file to the given path.

        Implement this in a way that will carefully
        update the target file with new metadata
        without destroying its other contents or structure.
        """

    def _get_property(self, key: Union[str, List[str]]) -> Optional[Any]:
        """Get a property from the data.

        Override this to e.g. rewrite the retrieved key
        (e.g. if everything relevant is in some suboject).
        """
        key_path = [key] if isinstance(key, str) else key

        curr = self._data
        for k in key_path:
            curr = curr.get(k)
            if curr is None:
                return None

        return curr

    def _set_property(self, key: Union[str, List[str]], value: Any) -> None:
        """Set a property in the data.

        Override this to e.g. rewrite the retrieved key
        (e.g. if everything relevant is in some suboject).
        """
        if not value:
            return
        key_path = [key] if isinstance(key, str) else key
        # create path on the fly if needed
        curr = self._data
        for key in key_path[:-1]:
            if key not in curr:
                curr[key] = {}
            curr = curr[key]
        curr[key_path[-1]] = value

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        self.name = metadata.name
        self.description = metadata.description

        if metadata.version:
            self.version = metadata.version

        if metadata.keywords:
            self.keywords = metadata.keywords
        self.authors = metadata.authors
        if metadata.maintainers:
            self.maintainers = metadata.maintainers

        self.license = metadata.license.value
        self.homepage = str(metadata.homepage)
        self.repository = str(metadata.repository)

    @staticmethod
    @abstractmethod
    def _from_person(person: Person) -> Any:
        """Convert a `Person` object into suitable target format."""

    # ----
    # individual magic getters and setters

    def _get_key(self, key):
        return self.direct_mappings.get(key) or key

    @property
    def name(self):
        """Return the name of the project."""
        return self._get_property(self._get_key("name"))

    @name.setter
    def name(self, name: str) -> None:
        """Set the name of the project."""
        self._set_property(self._get_key("name"), name)

    @property
    def version(self) -> Optional[str]:
        """Return the version of the project."""
        return self._get_property(self._get_key("version"))

    @version.setter
    def version(self, version: str) -> None:
        """Set the version of the project."""
        self._set_property(self._get_key("version"), version)

    @property
    def description(self) -> Optional[str]:
        """Return the description of the project."""
        return self._get_property(self._get_key("description"))

    @description.setter
    def description(self, description: str) -> None:
        """Set the description of the project."""
        self._set_property(self._get_key("description"), description)

    @property
    def authors(self):
        """Return the authors of the project."""
        return self._get_property(self._get_key("authors"))

    @authors.setter
    def authors(self, authors: List[Person]) -> None:
        """Set the authors of the project."""
        authors = [self._from_person(c) for c in authors]
        self._set_property(self._get_key("authors"), authors)

    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        return self._get_property(self._get_key("maintainers"))

    @maintainers.setter
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set the maintainers of the project."""
        maintainers = [self._from_person(c) for c in maintainers]
        self._set_property(self._get_key("maintainers"), maintainers)

    @property
    def keywords(self) -> Optional[List[str]]:
        """Return the keywords of the project."""
        return self._get_property(self._get_key("keywords"))

    @keywords.setter
    def keywords(self, keywords: List[str]) -> None:
        """Set the keywords of the project."""
        self._set_property(self._get_key("keywords"), keywords)

    @property
    def license(self) -> Optional[str]:
        """Return the license of the project."""
        return self._get_property(self._get_key("license"))

    @license.setter
    def license(self, license: Optional[str]) -> None:
        """Set the license of the project."""
        self._set_property(self._get_key("license"), license)

    @property
    def homepage(self) -> Optional[str]:
        """Return the homepage url of the project."""
        return self._get_property(self._get_key("homepage"))

    @homepage.setter
    def homepage(self, homepage: Optional[str]) -> None:
        """Set the homepage url of the project."""
        self._set_property(self._get_key("homepage"), homepage)

    @property
    def repository(self) -> Optional[str]:
        """Return the repository url of the project."""
        return self._get_property(self._get_key("repository"))

    @repository.setter
    def repository(self, repository: Optional[str]) -> None:
        """Set the repository url of the project."""
        self._set_property(self._get_key("repository"), repository)
