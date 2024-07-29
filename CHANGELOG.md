# Changelog

Here we provide notes that summarize the most important changes in each released version.

Please consult the changelog to inform yourself about breaking changes and security issues.

## [v0.4.3](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.4.3) <small>(2024-07-29)</small> { id="0.4.3" }

- update python dependencies
- update pre-commit hook versions
- fix package.json person validation
- update poetry, julia, and package.json person validation: entries without an email wont't raise an error, they will be ignored.

## [v0.4.2](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.4.2) <small>(2024-04-30)</small> { id="0.4.2" }

- fix rich logging bug for error messages and tracebacks

## [v0.4.1](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.4.1) <small>(2024-04-08)</small> { id="0.4.1" }

- fix package.json and mkdocs.yml validation bug about optional fields

## [v0.4.0](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.4.0) <small>(2024-03-08)</small> { id="0.4.0" }

- added separate `documentation` URL to Project metadata model
- added support for Julia `Project.toml` file
- added support for Fortran `fpm.toml` file
- added support for Java `pom.xml` file
- added support for MkDocs `mkdocs.yml` file
- added support for Rust `Cargo.toml` file

## [v0.3.1](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.3.1) <small>(2024-01-23)</small> { id="0.3.1" }

- fix setuptools license writing bug

## [v0.3.0](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.3.0) <small>(2024-01-12)</small> { id="0.3.0" }

- replace codemetapy with an in-house writer, which enables windows support

## [v0.2.1](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.2.1) <small>(2023-11-29)</small> { id="0.2.1" }

- **internal:** updated linters and dependencies
- **internal:** pin codemetapy version to 2.5.2 to avoid breaking changes
- fix bug caused by missing `config` section

## [v0.2.0](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.2.0) <small>(2023-11-29)</small> { id="0.2.0" }

- **internal:** Test refactoring
- **internal:** Pydantic 2 implementation
- Added `publication_author` field to Person model

## [v0.1.0](https://github.com/Materials-Data-Science-and-Informatics/somesy/tree/v0.1.0) <small>(2023-08-10)</small> { id="0.1.0" }

- First release
