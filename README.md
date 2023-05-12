# somesy

Somesy (**so**ftware **me**tadata **sy**nc) is a CLI tool to avoid messy software project metadata by keeping it in sync.

## Description

Many development tools allow or require to provide information about the software project they are used in.
These tools are often very specific to the programming-language and the task at hand and often come with their own configuration files.
Emerging best practices for [FAIR](https://www.go-fair.org/fair-principles/) software metadata require to add even _more_
files providing information such as the project name, description, version, repository url, license or authors.

If setting up the different files only once would be enough, there would not be an issue. But software is always in development and a moving target -
versions and maintainers can change, contributors come and go, the version number is regularly increased, the project can be moved to a different location.
Maintaining this kind of information and updating it in various files and formats used in the project by hand is _tedious, error-prone and time consuming_.
**Somesy automates the synchronization of general software project metadata** and frees your time to focus on your _actual_ work.

## Concepts

Because the same information is represented in different ways and more or less detail in different files, somesy requires to put all
project information in a **somesy-specific configuration section** is located in a supported **input file**.
Somesy will use this as the single source of truth for the supported project metadata fields
and can synchronize this information into different **output files**.

Somesy first **converts** the information as needed for an output, while trying to preserve as much information as possible.
Then it **carefully updates** the file, while keeping all other fields in the target file unchanged.
For files that are usually edited by hand, it will even make sure that the comments in your TOML and YAML files stay in place.

## Supported File Formats

Here is an overview of the supported files and formats.

| Input Formats  | Comment               |
| -------------- | --------------------- |
| pyproject.toml | `tool.somesy` section |
| package.json   | TBD                   |
| .somesy        | TBD                   |

| Output Formats                | Status |
| ----------------------------- | ------ |
| pyproject.toml _(poetry)_     | ✓      |
| pyproject.toml _(setuptools)_ | ✓      |
| package.json                  | TBD    |
| mkdocs.yml                    | TBD    |
| CITATION.cff                  | ✓      |
| codemeta.json                 | TBD    |

Somesy does not support **setuptools dynamic fields** in this version.

## Supported Metadata Fields

The below table shows which fields are mapped to corresponding other fields in the currently supported formats.

| Project Metadata | Poetry Config | SetupTools Config | CITATION.cff    |
| ---------------- | ------------- | ----------------- | --------------- |
| name             | name          | name              | title           |
| version          | version       | version           | version         |
| description      | description   | description       | abstract        |
| authors          | authors       | authors           | authors         |
| maintainers      | maintainers   | maintainers       | contact         |
| keywords         | keywords      | keywords          | keywords        |
| license          | license       | license           | license         |
| repository       | repository    | urls.repository   | repository_code |
| homepage         | homepage      | urls.homepage     | url             |

# Project Metadata

Somesy config has the information on what is the most important for metadata and standard columns between different file formats. Somesy config columns are explained below.

-   name: Software name - String
-   version: Software version - String
-   description: Software description - String
-   authors: Software authors - List of `Person`s
-   maintainers: Software maintainers - List of `Person`s
-   contributors: Software contributors - List of `Person`s
-   keywords: Keywords that explain the software - List of strings
-   license: SPDX string of the license - String in SPDX string format
-   repository: The repository URL - String in URL format
-   homepage: The software website - String in URL format

`Person` is a subclass of the Project Metadata, based on the CFF version 1.2.0 Person class. We added contribution relation fields to this `Person` class to appreciate all the contributions to the project. `Person` class fields:

-   address: The person's address. - String
-   affiliation: The person's affiliation. - String
-   alias: The person's alias. - String
-   city: The person's city. - String
-   country: The person's country abbreviation in two capital characters. - String
-   email: The person's email address. - String in email format
-   family-names: The person's family names. - String
-   fax: The person's fax number. - String
-   given-names: The person's given names. - String
-   name-particle: The person's name particle, e.g., a nobiliary particle or a preposition meaning 'of' or 'from' (for example, 'von' in 'Alexander von Humboldt'). - String
-   name-suffix: The person's name-suffix, e.g. 'Jr.' for Sammy Davis Jr. or 'III' for Frank Edwin Wright III. - String
-   orcid: The person's ORCID URL. - String in URL format
-   post_code: The person's post-code. - String
-   tel: The person's phone number. - String
-   website: The person's website. - String in URL format
-   contribution: Summary of how the person contributed to the project. - String
-   contribution_type: Contribution type of contributor using emoji from [all contributors](https://allcontributors.org/docs/en/emoji-key). - String in emoji name
-   contribution_begin: Beginning date of the contribution. - Date in YYYY-MM-DD format
-   contribution_end: Ending date of the contribution. - Date in YYYY-MM-DD format

Config fields have to adhere above restrictions. If not, somesy tool will raise errors.

## Getting Started

Somesy requires Python `>=3.8`.
You can install the package just as any other package into your
current Python environment using:

```
$ pip install git+ssh://git@github.com:Materials-Data-Science-and-Informatics/somesy.git
```

or, if you are adding it as a dependency into a poetry project:

```
$ poetry add git+ssh://git@github.com:Materials-Data-Science-and-Informatics/somesy.git
```

## Development

This project uses [Poetry](https://python-poetry.org/) for dependency management,
so you will need to have it
[installed](https://python-poetry.org/docs/master/#installing-with-the-official-installer)
for a development setup for working on this package.

Then you can run the following lines to setup the project:

```
$ git clone git@github.com:Materials-Data-Science-and-Informatics/somesy.git
$ cd somesy
$ poetry install
```

Common tasks are accessible via [poethepoet](https://github.com/nat-n/poethepoet),
which can be installed by running `poetry self add 'poethepoet[poetry_plugin]'`.

-   Use `poetry poe init-dev` after cloning to enable automatic linting before each commit.

-   Use `poetry poe lint` to run the same linters manually.

-   Use `poetry poe test` to run tests, add `--cov` to also show test coverage.

-   Use `poetry poe docs` to generate local documentation.

## Acknowledgements

<div>
<img style="vertical-align: middle;" alt="HMC Logo" src="https://github.com/Materials-Data-Science-and-Informatics/Logos/raw/main/HMC/HMC_Logo_M.png" width=50% height=50% />
&nbsp;&nbsp;
<img style="vertical-align: middle;" alt="FZJ Logo" src="https://github.com/Materials-Data-Science-and-Informatics/Logos/raw/main/FZJ/FZJ.png" width=30% height=30% />
</div>
<br />

This project was developed at the Institute for Materials Data Science and Informatics
(IAS-9) of the Jülich Research Center and funded by the Helmholtz Metadata Collaboration
(HMC), an incubator-platform of the Helmholtz Association within the framework of the
Information and Data Science strategic initiative.
