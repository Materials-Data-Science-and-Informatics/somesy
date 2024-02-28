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
[
![OpenSSF Best Practices](https://bestpractices.coreinfrastructure.org/projects/7701/badge)
](https://bestpractices.coreinfrastructure.org/projects/7701)
[
![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F-green)
](https://fair-software.eu)

<!-- --8<-- [start:abstract] -->

<div style="text-align: center;">
    <img alt="HMC Logo" src="https://github.com/Materials-Data-Science-and-Informatics/Logos/raw/main/Somesy/Somesy_Logo_Text.png" style="width: 50%; height: 50%;" />
</div>


# somesy

Somesy (**so**ftware **me**tadata **sy**nc) is a CLI tool to avoid messy software project metadata by keeping it in sync.

## Description

Many development tools either declare or need information about the software project they are used in, such as: the project name, description, version, repository url, license or project authors.
Most such tools come with configuration files and conventions that are specific to the programming language or chosen technology.
Emerging best practices for [FAIR](https://www.go-fair.org/fair-principles/) software metadata require to add even _more_ files where such metadata must be stated.

If good project metadata was a fire-and-forget issue, this would be acceptable, but software is never standing still - maintainers change, contributors come and go, the version number is regularly increased, the project might be moved to a different location.
Properly maintaining this kind of information in various files scattered around the project is usually _tedious, error-prone and time consuming manual labor_.

**Somesy automates the synchronization of software project metadata and frees your time to focus on your _actual_ work**.

<!-- --8<-- [end:abstract] -->

**You can find more information on configuring, using and contributing to `somesy` in the
[documentation](https://materials-data-science-and-informatics.github.io/somesy/main).**

<!-- --8<-- [start:quickstart] -->

## Getting Started

### Platform Support

Starting with version **0.3.0**, `somesy` supports Linux, MacOS and Windows.

Make sure that you use the latest version in order to avoid any problems.

### Installing somesy

Somesy requires Python `>=3.8`. To get a first impression, you can install the
latest stable version of somesy from PyPI using `pip`:

```bash
pip install somesy
```

### Configuring somesy

Yes, somesy is *another* tool with its own configuration. However, for your
project metadata it is hopefully the last file you need, and the only one you
have to think about, `somesy` will take care of the others for you!

To get started, create a file named `somesy.toml`:

<!-- --8<-- [start:somesytoml] -->
```toml
[project]
name = "my-amazing-project"
version = "0.1.0"
description = "Brief description of my amazing software."

keywords = ["some", "descriptive", "keywords"]
license = "MIT"
repository = "https://github.com/username/my-amazing-project"

# This is you, the proud author of your project:
[[project.people]]
given-names = "Jane"
family-names = "Doe"
email = "j.doe@example.com"
orcid = "https://orcid.org/0000-0000-0000-0001"
author = true      # is a full author of the project (i.e. appears in citations)
maintainer = true  # currently maintains the project (i.e. is a contact person)

# this person is an acknowledged contributor, but not author or maintainer:
[[project.people]]
given-names = "Another"
family-names = "Contributor"
email = "a.contributor@example.com"
orcid = "https://orcid.org/0000-0000-0000-0002"
# ... but for scientific publications, this contributor should be listed as author:
publication_author = true

[config]
verbose = true     # show detailed information about what somesy is doing
```
<!-- --8<-- [end:somesytoml] -->

Alternatively, you can also add the somesy configuration to an existing
`pyproject.toml`, `package.json`, `Project.toml`, or `fpm.toml` file. The somesy [manual](https://materials-data-science-and-informatics.github.io/somesy/main/manual/#somesy-input-file) contains examples showing how to do that.

### Using somesy

Once somesy is installed and configured, somesy can take over and manage your project metadata.
Now you can run `somesy` simply by using

```bash
somesy sync
```

The information in your `somesy.toml` is used as the **primary and
authoritative** source for project metadata, which is used to update all
supported (and enabled) *target files*. You can find an overview of supported
formats further below.

By default, `somesy` will create (if they did not exist) or update `CITATION.cff` and `codemeta.json` files in your repository.
If you happen to use

* `pyproject.toml` (in Python projects),
* `package.json` (in JavaScript projects),
* `Project.toml` (in Julia projects),
* `fpm.toml` (in Fortran projects),
* `pom.xml` (in Java projects),
* `mkdocs.yml` (in projects using MkDocs),
* `Cargo.toml` (in Rust projects)

then somesy would also update the respective information there.

You can see call available options with `somesy --help`,
all of these can also be conveniently set in your `somesy.toml` file.

### Somesy as a pre-commit hook

<!-- --8<-- [start:precommit] -->

We highly recommend to use `somesy` as a [pre-commit hook](https://pre-commit.com/).
A pre-commit hook runs on every commit to automatically point out issues or fix them on the spot,
so if you do not use pre-commit in your project yet, you should start today!
When used this way, `somesy` can fix most typical issues with your project
metadata even before your changes can leave your computer.

To add `somesy` as a pre-commit hook, add it to your `.pre-commit-config.yaml`
file in the root folder of your repository:

```yaml
repos:
  # ... (your other hooks) ...
  - repo: https://github.com/Materials-Data-Science-and-Informatics/somesy
    rev: "v0.3.0"
    hooks:
      - id: somesy
```

Note that `pre-commit` gives `somesy` the [staged](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F) version of files,
so when using `somesy` with pre-commit, keep in mind that

* if `somesy` changed some files, you need to `git add` them again (and rerun pre-commit)
* if you explicitly run `pre-commit`, make sure to `git add` all changed files (just like before a commit)

<!-- --8<-- [end:precommit] -->

## Supported File Formats

Here is an overview of all the currently supported files and formats.

| Input Formats  | Status | | Target Formats                | Status |
| -------------- | ------ |-| ----------------------------- | ------ |
| (.)somesy.toml | ✓      | | pyproject.toml _(poetry)_     | ✓      |
| pyproject.toml | ✓      | | pyproject.toml _(setuptools)_ | ✓(1.)  |
| package.json   | ✓      | | package.json _(JavaScript)_   | ✓(2.)  |
| Project.toml   | ✓      | | Project.toml _(Julia)_        | ✓      |
| fpm.toml       | ✓      | | fpm.toml _(Fortran)_          | ✓(3.)  |
|                | ✓      | | pom.toml _(Java)_             | ✓(4.)  |
| Cargo.toml     | ✓      | | Cargo.toml _(Rust)_           | ✓      |
|                |        | | mkdocs.yml                    | ✓(5.)  |
|                |        | | CITATION.cff                  | ✓      |
|                |        | | codemeta.json                 | ✓(6.)  |

**Notes:**

1. note that `somesy` does not support setuptools *dynamic fields*
2. `package.json` only supports one author, so `somesy` will pick the *first* listed author
3. `fpm.toml` only supports one author and maintainer, so `somesy` will pick the *first* listed author and maintainer
4. `pom.xml` has no concept of `maintainers`, but it can have multiple licenses (somesy only supports one main project license)
5. `mkdocs.yml` is a bit special, as it is not a project file, but a documentation file. `somesy` will only update it if it exists and is enabled in the configuration
6. unlike other targets, `somesy` will *re-create* the `codemeta.json` (i.e. do not edit it by hand!)

<!-- --8<-- [end:quickstart] -->

<!-- --8<-- [start:citation] -->

## How to Cite

If you want to cite this project in your scientific work,
please use the [citation file](https://citation-file-format.github.io/)
in the [repository](https://github.com/Materials-Data-Science-and-Informatics/somesy/blob/main/CITATION.cff).

<!-- --8<-- [end:citation] -->
<!-- --8<-- [start:acknowledgements] -->

## Acknowledgements

We kindly thank all
[authors and contributors](https://materials-data-science-and-informatics.github.io/somesy/latest/credits).


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
