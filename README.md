![Project status](https://img.shields.io/badge/project%20status-alpha-%23ff8000)
[
![Docs](https://img.shields.io/badge/read-docs-success)
](https://materials-data-science-and-informatics.github.io/somesy)
[
![CI](https://img.shields.io/github/actions/workflow/status/Materials-Data-Science-and-Informatics/somesy/ci.yml?branch=main&label=ci)
](https://github.com/Materials-Data-Science-and-Informatics/somesy/actions/workflows/ci.yml)
[
![Test Coverage](https://materials-data-science-and-informatics.github.io/somesy/main/coverage_badge.svg)
](https://materials-data-science-and-informatics.github.io/somesy/main/coverage)
[
![Docs Coverage](https://materials-data-science-and-informatics.github.io/somesy/main/interrogate_badge.svg)
](https://materials-data-science-and-informatics.github.io/somesy)
[
![PyPIPkgVersion](https://img.shields.io/pypi/v/somesy)
](https://pypi.org/project/somesy/)

<!-- --8<-- [start:abstract] -->

# SoMeSy

**SoMeSy** (**So**ftware **Me**tadata **Sy**nc) is a CLI tool to keep project metadata organized and in sync.

## Description

To preserve, dicover, reuse and credit software, rich metadata is the key. Best practices for [FAIR](https://www.go-fair.org/fair-principles/) software require metadata to be present at different locations (e.g. tool and programming-language specific configuration files), and mapped according to different standards (e.g. [Citation.cff](https://citation-file-format.github.io/) or [Codemeta](https://codemeta.github.io/)).

Software is always in development - versions and maintainers can change, contributors come and go, the version number is regularly increased, the project can be moved to a different location. Consequently software metadata is a moving target and needs frequent updates. This can be _tedious, error-prone and time consuming_ if done manually. Then software project metadata is often rendered incomplete, ambiguous or contradictory over time.

**SoMeSy automates management and synchronization of software project metadata.**

_With using SoMeSy, you update your metadata easily and keep it in order. SoMeSy automatically syncs metadata between different commonly used standards and lets you focus on what matters to you: your actual work._

## Concepts

Providing rich metadata for you software project, requires representing it differently and at different places in parallel. SoMeSy uses a **SoMeSy-specific input section** in your **input file** as a ground truth. Here all relevant project metadata is stored and synchronized to different desired **output files**.

Somesy first **converts** the information as needed for an output, while trying to preserve as much information as possible. Then it **carefully updates** the file, while keeping all other fields in the target file unchanged. For For files that are usually edited by hand, it will even make sure that the comments in your TOML and YAML files stay in place.

## Supported File Formats

Here is an overview of the supported files and formats.

| Input Formats  | Comment               |
| -------------- | --------------------- |
| pyproject.toml | `tool.somesy` section |
| package.json   | TBD                   |
| .somesy.toml   | ✓                     |

| Output Formats                | Status |
| ----------------------------- | ------ |
| pyproject.toml _(poetry)_     | ✓      |
| pyproject.toml _(setuptools)_ | ✓      |
| package.json                  | TBD    |
| mkdocs.yml                    | TBD    |
| CITATION.cff                  | ✓      |
| codemeta.json                 | ✓      |

**Warning for setuptools users:** Somesy does not support _setuptools dynamic fields_ in this version.

## Supported Metadata Fields

The below table shows which fields are mapped to corresponding other fields in the currently supported formats. Some of the metadata fields are required inputs in the somesy input file. `somesy` will give an error if required fields are not filled.

| Project Metadata<br> (SoMeSy input) | Poetry Config | SetupTools Config | CITATION.cff    | Requirement |
| ----------------------------------- | ------------- | ----------------- | --------------- | ----------- |
| name                                | name          | name              | title           | _required_  |
| version                             | version       | version           | version         | optional    |
| description                         | description   | description       | abstract        | _required_  |
| authors                             | authors       | authors           | authors         | _required_  |
| maintainers                         | maintainers   | maintainers       | contact         | optional    |
| keywords                            | keywords      | keywords          | keywords        | optional    |
| license                             | license       | license           | license         | _required_  |
| repository                          | repository    | urls.repository   | repository_code | optional    |
| homepage                            | homepage      | urls.homepage     | url             | optional    |

## Project Metadata

SoMeSy input requires the following information to satisfy the currently supported standards:

| Field       | Explanation                | IRI to external reference | supported datatype |
| ----------- | -------------------------- | ------------------------- | ------------------ |
| name        | name of software project   |                           | String             |
| version     | current version of project |                           | String             |
| description | description of project     |                           | String             |
| authors     | software authors           |                           | List of `Person`s  |
| maintainers | maintainers of software    |                           | List of `Person`s  |
| authors     | contributors to software   |                           | List of `Person`s  |
| keywords    | keywords for the software  |                           | List of String     |
| license     | license of software        |                           | String             |
| repository  | repository URL of software |                           | String             |
| homepage    | homepage URL of software   |                           | String             |

`Person` is a subclass of the Project Metadata, based on the [Citation.CFF version 1.2.0 Person class](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md#definitionsperson). We added contribution relation fields to this `Person` class to differentiate different kinds of contributions to the project. `Person` class fields contain:

| Field              | Explanation                                                                                                          | IRI to external reference                                                           | Supported Datatype        |
| ------------------ | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------- |
| address            | The person's address.                                                                                                |                                                                                     | String                    |
| affiliation        | The person's affiliation.                                                                                            |                                                                                     | String                    |
| alias              | The person's alias.                                                                                                  |                                                                                     | String                    |
| city               | The person's city.                                                                                                   |                                                                                     | String                    |
| country            | The person's country abbreviation in two capital characters.                                                         | [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) | String                    |
| email              | The person's email address.                                                                                          |                                                                                     | String                    |
| family-names       | The person's family names.                                                                                           |                                                                                     | String                    |
| fax                | The person's fax number.                                                                                             |                                                                                     | String                    |
| given-names        | The person's given names.                                                                                            |                                                                                     | String                    |
| name-particle      | The person's name particle, e.g., a preposition meaning 'of' or 'from'.                                              |                                                                                     | String                    |
| name-suffix        | The person's name-suffix, e.g. 'Jr.' for Sammy Davis Jr. or 'III' for Frank Edwin Wright III.                        |                                                                                     | String                    |
| orcid              | The person's ORCID URL.                                                                                              | [ORCID](https://orcid.org/)                                                         | String                    |
| post_code          | The person's post-code.                                                                                              |                                                                                     | String                    |
| tel                | The person's phone number.                                                                                           |                                                                                     | String                    |
| website            | The person's website.                                                                                                |                                                                                     | String                    |
| contribution       | Summary of how the person contributed to the project.                                                                |                                                                                     | String                    |
| contribution_type  | Contribution type of contributor using emoji from [all contributors](https://allcontributors.org/docs/en/emoji-key). | [All Contributors Emoji Key](https://allcontributors.org/docs/en/emoji-key)         | String or List of String  |
| contribution_begin | Beginning date of the contribution.                                                                                  |                                                                                     | Date in YYYY-MM-DD format |
| contribution_end   | Ending date of the contribution.                                                                                     |                                                                                     | Date in YYYY-MM-DD format |

Input fields have to adhere above restrictions. If not, somesy tool will raise errors.

<!-- --8<-- [end:abstract] -->
<!-- --8<-- [start:quickstart] -->

## Getting Started

### Installing somesy

Somesy requires Python `>=3.8`. You can install the package just as any other package into your current Python environment using:

```bash
$ pip install git+ssh://git@github.com:Materials-Data-Science-and-Informatics/somesy.git
```

or, if you are adding it as a dependency into a poetry project:

```bash
$ poetry add git+ssh://git@github.com:Materials-Data-Science-and-Informatics/somesy.git
```

### Use as a CLI tool

After the installation with pip, you can use somesy as a CLI tool.

You can see all supported somesy CLI command options using `somesy --help`.

The `somesy sync` command checks input file in the working directory by default.

The files `.somesy.toml` and `pyproject.toml` are supported as input files, `somesy` picks the first one (in listed order) which provides somesy configuration and metadata.

Currently, there are 3 output targets for `somesy sync` command, `CITATION.cff`, `codemeta.json` and `pyproject.toml` (either in poetry or setuptools format), and all are synced by default.

The `codemeta.json` and `CITATION.cff` are automatically created if the respective file does not exist yet,
but a `pyproject.toml` must be created beforehand either in poetry or setuptools format (as somesy does not know which is preferred).

If you do not want that somesy creates/synchronizes these files, you can disable them by CLI options or in your somesy configuration.

Configuration of somesy in an input file overrides the defaults, and options passed as CLI arguments override the configuration.

`somesy sync` is designed to be used as a pre-commit hook, so it does not give any output unless there is an error or one of the related flags is set. Also, `somesy` will give an error if there is no output to sync.

You can save your CLI inputs to your input file or you can use `somesy config init` command. It records CLI options for `somesy sync` command to given input file. All options are prompted with their default values. The options are saved under [config.cli] table in the input file. You can change the options later by editing the input file. Unlike `somesy sync` command, `somesy config init` command shows the basic output of the command, and shows more if verbose or debug is selected in prompt.

`somesy sync` command options:

| Command     | Option                  | Option input        | Description                     |
| ----------- | ----------------------- | ------------------- | ------------------------------- |
| somesy sync | --input-file, -i        | input file path     | set input file                  |
| somesy sync | --no-sync-cff, -C       | -                   | Do not sync CITATION.cff file   |
| somesy sync | --cff-file, -c          | cff file path       | set CITATION.cff file to sync   |
| somesy sync | --no-sync-pyproject, -P | -                   | Do not sync pyproject file      |
| somesy sync | --pyproject-file, -p    | pyproject file path | set pyproject file to sync      |
| somesy sync | --no-sync-codemeta, -M  | -                   | Do not sync codemeta file       |
| somesy sync | --codemeta-file, -m     | codemeta file path  | set codemeta file to sync       |
| somesy sync | --show-info, -s         | -                   | show basic information messages |
| somesy sync | --verbose, -v           | -                   | show verbose messages           |
| somesy sync | --debug, -d             | -                   | show debug messages             |

### Use as a Pre-commit hook

`somesy` can be used as a [pre-commit hook](https://pre-commit.com/). A pre-commit hook runs on every commit to automatically point out issues and/or fixing them. Thus, `somesy` syncs your data in every commit in a deterministic way.
If you already use pre-commit, you can add somesy as a pre-commit hook. For people who are new to pre-commit, you can create a `.pre-commit-config.yaml` file in the root folder of your repository. You can set CLI options in `args` as in the example below, or provide configuration in your input file (`.somesy` or `pyproject.toml`).

```yaml
repos:
  - repo: https://github.com/Materials-Data-Science-and-Informatics/somesy
    rev: "0.1.0"
    hooks:
      - id: somesy
        args: ["-C", "-p", "~/xx/xx/pyproject.toml"]
```

### Somesy input file

This repository has a `.somesy.toml` file that can be used as a example.
You can check this additional example for somesy project metadata inputs.
Please pay attention to the toml table titles for each file example, the input itself is the same.

_.somesy.toml_ example:

```toml
[project]
name = "test"
version = "0.1.0"
description = "Test description."
authors = [
    {family-names = "Doe", given-names= "John", email = "test@test.test", orcid = "https://orcid.org/0000-0001-2345-5678", contribution = "The main author, maintainer and tester.", contribution_begin = "2023-03-01", contribution_type = "code"},
]
maintainers = [
    {family-names = "Doe", given-names= "John", email = "test@test.test", orcid = "https://orcid.org/0000-0001-2345-5678", contribution = "The main author, maintainer and tester.", contribution_begin = "2023-03-01", contribution_type = "code"},
]
contributors = [
    {family-names = "Doe", given-names= "John", email = "test@test.test", orcid = "https://orcid.org/0000-0001-2345-5678", contribution = "The main author, maintainer and tester.", contribution_begin = "2023-03-01", contribution_type = "code"},
    {family-names = "Dow", given-names= "John", email = "test2@test.test", orcid = "https://orcid.org/0000-0012-3456-7890", contribution = "Reviewer", contribution_begin = "2023-03-01", contribution_type = "review"},
]
keywords = ["key", "word"]
license = "MIT"
repository = "https://github.com/xx/test"
homepage = "https://xx.github.io/test"

[config.cli]
no_sync_cff = false
cff_file = "CITATION.cff"
no_sync_pyproject = false
pyproject_file = "pyproject.toml"
show_info = false
verbose = false
debug = true
```

_pyproject.toml_ example:

```toml
[tool.somesy.project]
name = "test"
version = "0.1.0"
description = "Test description."
authors = [
    {family-names = "Doe", given-names= "John", email = "test@test.test", orcid = "https://orcid.org/0000-0001-2345-5678", contribution = "The main author, maintainer and tester.", contribution_begin = "2023-03-01", contribution_type = "code"}
]
maintainers = [
    {family-names = "Doe", given-names= "John", email = "test@test.test", orcid = "https://orcid.org/0000-0001-2345-5678", contribution = "The main author, maintainer and tester.", contribution_begin = "2023-03-01", contribution_type = "code"}
]
contributors = [
    {family-names = "Doe", given-names= "John", email = "test@test.test", orcid = "https://orcid.org/0000-0001-2345-5678", contribution = "The main author, maintainer and tester.", contribution_begin = "2023-03-01", contribution_type = "code"},
    {family-names = "Dow", given-names= "John", email = "test2@test.test", orcid = "https://orcid.org/0000-0012-3456-7890", contribution = "Reviewer", contribution_begin = "2023-03-01", contribution_type = "review"}
]
keywords = ["key", "word"]
license = "MIT"
repository = "https://github.com/xx/test"
homepage = "https://xx.github.io/test"

[tool.somesy.config.cli]
no_sync_cff = false
cff_file = "CITATION.cff"
no_sync_pyproject = false
pyproject_file = "pyproject.toml"
show_info = false
verbose = false
debug = true
```

<!-- --8<-- [end:quickstart] -->

## Development

This project uses [Poetry](https://python-poetry.org/) for dependency management,
so you will need to have it
[installed](https://python-poetry.org/docs/master/#installing-with-the-official-installer)
for a development setup for working on this package.

Then you can run the following lines to setup the project:

```bash
$ git clone git@github.com:Materials-Data-Science-and-Informatics/somesy.git
$ cd somesy
$ poetry install
```

Common tasks are accessible via [poethepoet](https://github.com/nat-n/poethepoet),
which can be installed by running `poetry self add 'poethepoet[poetry_plugin]'`.

- Use `poetry poe init-dev` after cloning to enable automatic linting before each commit.

- Use `poetry poe lint` to run the same linters manually.

- Use `poetry poe test` to run tests, add `--cov` to also show test coverage.

- Use `poetry poe docs` to generate local documentation.

<!-- --8<-- [start:citation] -->

## How to Cite

If you want to cite this project in your scientific work,
please use the [citation file](https://citation-file-format.github.io/)
in the [repository](https://github.com/Materials-Data-Science-and-Informatics/somesy/blob/main/CITATION.cff).

<!-- --8<-- [end:citation] -->
<!-- --8<-- [start:acknowledgements] -->

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

<!-- --8<-- [end:acknowledgements] -->
