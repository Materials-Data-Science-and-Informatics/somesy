# User Manual

This is the reference manual for `somesy` providing details about its
configuration and behavior.

Before you proceed, make sure you have read the [introduction](./index.md)
and the [quick-start guide](./quickstart.md).

## Somesy Metadata Schemas

Because the same information is represented in different ways and more or less
detail in different files, somesy requires to put all project information in a
**somesy-specific input section** is located in a supported **input file**.
Somesy will use this as the single source of truth for the supported project
metadata fields and can synchronize this information into different **target
files**.

!!! info

    The somesy schemas are designed to allow expressing metadata in the most
    useful and rich form, i.e. the best form that some of the target formats
    supports.

Somesy project metadata consists of two main schemas - one schema for describing
people (authors, maintainers, contributors), and a schema describing the
project.

The somesy metadata fields (especially for people) are mostly based on
[Citation File Format 1.2](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md), with some custom extensions.
Somesy will try staying aligned with future revisions of `CITATION.cff`, unless
for technical or practical reasons a deviation or extension is justified.

One useful distinction somesy does in contrast to many target formats is to
allow stating all people in one place. If a person is both an author and a
maintainer, that person does not need to be listed with all information twice.

This is done by adding the `author` and `maintainer` flags that can be set for
every listed person. Somesy will take care of duplicating the entries where this
is needed.

Furthermore `somesy` allows to provide more fine-grained information about the
contribution of a person and acknowledge contributors that are neither full
authors or maintainers.

!!! note

    Currently, provided information about contributors that are neither authors
    nor maintainers, and all the detailed information on the contributions is
    not used.

    Nevertheless, **we encourage** tracking granular contributor and contribution information
    in order to motivate and acknowledge also minor or invisible contributions to a projects.

    Once CITATION.cff introduces corresponding mechanisms,
    `somesy` will be aligned with the corresponding capabilities.
    Furthermore, `somesy` might support the
    [allcontributors](https://allcontributors.org/) tool as a target in the future.

### Schemas Overview

Here is an overview of the schemas used in somesy.

```python exec="on"
# NOTE: this is an ugly ad-hoc solution, but it does the job ;)
# Just make sure to check docs when changing the models!
import json
from io import StringIO
from somesy.core.models import SomesyInput, ProjectMetadata, Person, SomesyConfig
from pydantic_core import PydanticUndefined
from typing_extensions import get_args

def pp_type(th):
    # NOTE: this does not work correctly with non-trivial unions!
    while args := get_args(th):
        th = args[0]
    return th.__name__

def fmt_desc(desc, pref=""):
    if not desc:
        return ""
    return "\n".join(map(lambda x: pref + x.strip(), desc.split("\n")))


def model2md(m, out = None):
    out = out or StringIO()

    out.write(f'=== "{m.__name__}"\n\n')
    out.write(fmt_desc(m.__doc__, pref="\t"))
    out.write("\t\n\n")
    out.write("\t| Field | Type | Required? | Default | Description |\n")
    out.write("\t| ----- | ---- | --------- | ------- | ----------- |\n")
    for n, fld in m.model_fields.items():
        t = pp_type(fld.annotation)
        r = "**yes**" if fld.is_required() else "no"
        dv = fld.default
        if dv is not None and dv != PydanticUndefined:
            v = json.dumps(fld.default, default=str)
        else:
            v = ""
        d = fmt_desc(fld.description)
        out.write(f"\t| {n} | {t} | {r} | {v} | {d} |\n")
    out.write("\n")

    return out

print(model2md(SomesyInput).getvalue())
print(model2md(ProjectMetadata).getvalue())
print(model2md(Person).getvalue())
print(model2md(SomesyConfig).getvalue())
```

### Metadata Mapping

From its own schema `somesy` must convert the information into the target formats.
The following tables sketch how fields are mapped to corresponding other fields in
some of the currently supported formats. Bold field names are mandatory, the others are optional.

=== "Person Metadata"

    | Somesy Field     | Poetry Config | SetupTools Config | Java POM     | Julia Config | Fortran Config | package.json | mkdocs.yml | Rust Config    | CITATION.cff    | CodeMeta        |
    | ---------------- | ------------- | ----------------- | ------------ | ------------ | -------------- | ------------ | ---------- | -------------- | --------------- | -------------- |
    |                  |               |                   |              |              |                |              |            |                |                 |                |
    | **given-names**  | name+email    | name              | name         | name+email   | name+email     | name         | name+email | name+email     | givenName       | name+email     |
    | **family-names** | name+email    | name              | name         | name+email   | name+email     | name         | name+email | name+email     | familyName      | name+email     |
    | **email**        | name+email    | email             | email        | name+email   | name+email     | email        | name+email | name+email     | email           | name+email     |
    | orcid            | -             | -                 | url          | -            | -              | url          | -          | -              | id              | -              |
    | *(many others)*  | -             | -                 | -            | -            | -              | -            | -          | -              | *(same)*        | -              |

=== "Project Metadata"

    | Somesy Field      | Poetry Config | SetupTools Config  | Java POM                        | Julia Config | Fortran Config | package.json | mkdocs.yml       | Rust Config     | CITATION.cff    | CodeMeta          |
    | ----------------- | ------------- | ------------------ | ------------------------------- | ------------ | -------------- | ------------ | ---------------- | --------------- | --------------- | ----------------- |
    |                   |               |                    |                                 |              |                |              |                  |                 |                 |                   |
    | **name**          | name          | name               | name                            | name         | name           | name         | site_name        | name            | title           | name              |
    | **description**   | description   | description        | description                     | -            | description    | description  | site_description | description     | abstract        | description       |
    | **license**       | license       | license            | licenses.license                | -            | license        | license      | -                | license         | license         | license           |
    | **version**       | version       | version            | version                         | version      | version        | version      | -                | version         | version         | version           |
    |                   |               |                    |                                 |              |                |              |                  |                 |                 |                   |
    | ***author=true*** | authors       | authors            | developers                      | authors      | author         | author       | site_author      | authors         | authors         | author            |
    | *maintainer=true* | maintainers   | maintainers        | -                               | -            | maintainer     | maintainers  | -                | -               | contact         | maintainer        |
    | *people*          | -             | -                  | -                               | -            | -              | contributors | -                | -               | -               | contributor       |
    |                   |               |                    |                                 |              |                |              |                  |                 |                 |                   |
    | keywords          | keywords      | keywords           | -                               | -            | keywords       | keywords     | -                | keywords        | keywords        | keywords          |
    | homepage          | homepage      | urls.homepage      | urls                            | -            | homepage       | homepage     | site_url         | homepage        | url             | url               |
    | repository        | repository    | urls.repository    | scm.url                         | -            | -              | repository   | repo_url         | repository      | repository_code | codeRepository    |
    | documentation     | documentation | urls.documentation | distributionManagement.site.url | -            | -              | -            | -                | documentation   | -               | buildInstructions |


Note that the mapping is often not 1-to-1. For example, CITATION.cff allows rich
specification of author contact information and complex names. In contrast,
poetry only supports a simple string with a name and email (like in git commits)
to list authors and maintainers. **Therefore somesy sometimes must do much more
than just move or rename fields**. This means that giving a clean and complete
mapping overview is not feasible. In case of doubt or confusion, please open an
issue or consult the `somesy` code.

## The somesy CLI tool

You can see all supported somesy CLI command options using `somesy --help`:

```bash exec="true" source="above" result="ansi"
somesy sync --help
```

Everything that can be configured as a CLI flag can also be set in a `somesy.toml` file
in the `[config]` section. CLI arguments set in an input file override the
defaults, while options passed as CLI arguments override the configuration.

Without an input file specifically provided, somesy will check if it can find a valid

* `.somesy.toml`
* `somesy.toml`
* `pyproject.toml` (in `tool.somesy` section)
* `Project.toml` (in `tool.somesy` section)
* `fpm.toml` (in `tool.somesy` section)
* `package.json` (in `somesy` section)
* `Cargo.toml` (in `package.metadata.somesy` section)

which is located in the current working directory. If you want to provide
the somesy input file from a different location, you can pass it with the `-i` option.

### Somesy Input File

Here is an example how project metadata and `somesy` can be configured using
one of the supported input formats:

=== "somesy.toml"

    --8<-- "README.md:somesytoml"

=== "pyproject.toml"

    ```toml
    [tool.poetry]
    name = "my-amazing-project"
    version = "0.1.0"
    ...

    [tool.somesy.project]
    name = "my-amazing-project"
    version = "0.1.0"
    description = "Brief description of my amazing software."

    keywords = ["some", "descriptive", "keywords"]
    license = "MIT"
    repository = "https://github.com/username/my-amazing-project"

    # This is you, the proud author of your project
    [[tool.somesy.project.people]]
    given-names = "Jane"
    family-names = "Doe"
    email = "j.doe@example.com"
    orcid = "https://orcid.org/0000-0000-0000-0001"
    author = true      # is a full author of the project (i.e. appears in citations)
    maintainer = true  # currently maintains the project (i.e. is a contact person)

    # this person is a acknowledged contributor, but not author or maintainer:
    [[tool.somesy.project.people]]
    given-names = "Another"
    family-names = "Contributor"
    email = "a.contributor@example.com"
    orcid = "https://orcid.org/0000-0000-0000-0002"

    [tool.somesy.config]
    verbose = true     # show detailed information about what somesy is doing
    ```

=== "Project.toml"
    ```toml
    name = "my-amazing-project"
    version = "0.1.0"
    uuid = "c7e460c6-3f3e-11ec-8d3d-0242ac130003"

    [deps]
    ...

    [tool.somesy.project]
    name = "my-amazing-project"
    version = "0.1.0"
    description = "Brief description of my amazing software."

    keywords = ["some", "descriptive", "keywords"]
    license = "MIT"
    repository = "https://github.com/username/my-amazing-project"

    # This is you, the proud author of your project
    [[tool.somesy.project.people]]
    given-names = "Jane"
    family-names = "Doe"
    email = "j.doe@example.com"
    orcid = "https://orcid.org/0000-0000-0000-0001"
    author = true      # is a full author of the project (i.e. appears in citations)
    maintainer = true  # currently maintains the project (i.e. is a contact person)

    # this person is a acknowledged contributor, but not author or maintainer:
    [[tool.somesy.project.people]]
    given-names = "Another"
    family-names = "Contributor"
    email = "a.contributor@example.com"
    orcid = "https://orcid.org/0000-0000-0000-0002"

    [tool.somesy.config]
    verbose = true     # show detailed information about what somesy is doing
    ```

=== "fpm.toml"
    ```toml
    name = "my-amazing-project"
    version = "0.1.0"

    [tool.somesy.project]
    name = "my-amazing-project"
    version = "0.1.0"
    description = "Brief description of my amazing software."

    keywords = ["some", "descriptive", "keywords"]
    license = "MIT"
    repository = "https://github.com/username/my-amazing-project"

    # This is you, the proud author of your project
    [[tool.somesy.project.people]]
    given-names = "Jane"
    family-names = "Doe"
    email = "j.doe@example.com"
    orcid = "https://orcid.org/0000-0000-0000-0001"
    author = true      # is a full author of the project (i.e. appears in citations)
    maintainer = true  # currently maintains the project (i.e. is a contact person)

    # this person is a acknowledged contributor, but not author or maintainer:
    [[tool.somesy.project.people]]
    given-names = "Another"
    family-names = "Contributor"
    email = "a.contributor@example.com"
    orcid = "https://orcid.org/0000-0000-0000-0002"

    [tool.somesy.config]
    verbose = true     # show detailed information about what somesy is doing
    ```

=== "package.json"

    ```json
    {
      "name": "my-amazing-project",
      "version": "0.1.0",
      ...

      "somesy": {
        "project": {
          "name": "my-amazing-project",
          "version": "0.1.0",
          "description": "Brief description of my amazing software.",
          "keywords": ["some", "descriptive", "keywords"],
          "license": "MIT",
          "repository": "https://github.com/username/my-amazing-project",
          "people": [
            {
              "given-names": "Jane",
              "family-names": "Doe",
              "email": "j.doe@example.com",
              "orcid": "https://orcid.org/0000-0000-0000-0001",
              "author": true,
              "maintainer": true
            },
            {
              "given-names": "Another",
              "family-names": "Contributor",
              "email": "a.contributor@example.com",
              "orcid": "https://orcid.org/0000-0000-0000-0002"
            }
          ]
        },
        "config": {
          "verbose": true
        }
      }
    }
    ```

All possible metadata fields and configuration options are explained further [above](#schemas-overview).

### pre-commit hook

--8<-- "README.md:precommit"

### Synchronization

Unless configured otherwise, `somesy` will create `CITATION.cff`
and `codemeta.json` files if they do not exist.
Other supported files (such as `pyproject.toml` or `package.json`)
are updated if they already exist in your repository.

If you do not want that somesy creates/synchronizes these files,
you can disable them by CLI options or in your somesy configuration.

## Metadata Update Logic

In this section we explain a few details about how `somesy` updates metadata.

### Somesy Inputs Override Target Values

In general, `somesy` updates fields in target files and formats
based on the information stated in the `somesy.toml`.

It will convert the metadata into the form needed for a target,
while trying to preserve as much information as possible. Then it **carefully
updates** the file, while keeping all other fields in the target file unchanged.

In most cases, `somesy` will try not to interfere with other values, metadata
and configuration you might have in a target file.

!!! info

    For typically manually-edited files, it will even make sure that the
    comments stay in place! (currently works for TOML)

!!! tip

    Only edit target files manually to add or update fields
    that `somesy` does **not** understand or care about!

!!! warning

    All changes in target files you do to fields `somesy` *does* understand will be
    overwritten the next time you run somesy.

!!! tip

    * update all project metadata supported by `somesy` in the `somesy.toml`
    * update other metadata directly in the target files

### Checking Somesy Results

Note that `somesy` in general will try doing a good job and hopefully will in
most cases, but in certain tricky situations it might not be able to figure out
the and needed changes correctly.

!!! danger

    Always check the files that somesy synchronized look right
    before committing/pushing the changes!

Doing what `somesy` does both convenient and right is (maybe surprisingly to
you) quite difficult, so while somesy should save you quite some tedious work,
you should not use it blindly. You have been warned!

### Person Identification Heuristics

One frequent source of high-level project metadata changes is fluctuation of
authors, maintainers and contributors and eventual changes of the respective
contact and identification information.

Somesy will try its best to keep track of persons involved in your software
project, but to avoid possible problems and unexpected behavior, it might be
helpful to **understand how somesy determines whether two metadata records
describe the same real person**.

When somesy compares two metadata records about a person, it will proceed as follows:

1. If both records contain an ORCID, then the person is the same if the attached ORCIDs are equal, and different if it is not.
2. Otherwise, if both records have an attached email address, and it is the same email, then they are the same person.
3. Otherwise, the records are considered to be about the same person if they agree on the full name (i.e. given, middle and family name sequence).

!!! tip

    State ORCIDs for persons whenever possible (i.e. the person has an ORCID)!

!!! tip

    If a person does not have an ORCID, suggest that they should create one!

Somesy will usually correctly understand cases such as:

1. An ORCID being added to a person (i.e. if it was not present before)
2. A changed email address (if the name stays the same)
3. A changed name (if the email address stays the same)
4. Any other relevant metadata attached to the person

Nevertheless, you should **check the changes somesy does** before committing them to your repository,
especially **after you significantly modified your project metadata**.

!!! warning

    Note that changing the ORCID will not be recognized,
    because ORCIDs are assumed to be unique per person.

If you initially have stated an incorrect ORCID for a person and then change it, **somesy will think that this is a new person**.
Therefore, **in such a case you will need to fix the ORCID in all configured somesy targets** either
before running somesy (so somesy will not create new person entries), or
after running somesy (to remove the duplicate entries with the incorrect ORCID).

!!! warning

    Person identification and merging is not applied to standards with free text fields for authors or maintainers, such as `fpm.toml`.

### Codemeta

While `somesy` is modifying existing files for most supported formats and implements
features such as person identification and merging,
[CodeMeta](https://codemeta.github.io/) is implemented differently.

As that `codemeta.json` is a [**JSON-LD**](https://json-ld.org/) file, it actually represents a graph,
has various equally valid representations in a JSON file.
Thus, supporting the same features as for other formats is technically much more
challenging, if at all feasible. Therefore, for the time being, we regenerate the
`codemeta.json` file directly from the source file, in order to avoid data inconsistency
due to many pitfalls hiding in the details of the format.

!!! warning

    The `codemeta.json` is overwritten and regenerated from scratch every time you `sync`,
    so **do not edit it** if you have the codemeta target enabled in `somesy`!

As `codemeta.json` is considered a technical "backend-format" derived from other
inputs, in most cases you probably do not need or should edit it by hand anyway.

Of course, you are welcome to contribute an improved CodeMeta writer for somesy that can correctly
understand and update the linked data graph which the `codemeta.json` file represents!

## Using somesy to insert metadata into project documentation

While `somesy` can synchronize structured metadata files and formats, there is a common case that cannot be covered by the `sync` command - when project metadata should appear in plain text documents, such as documentation files and web pages.

As for documentation the needs and used tooling in different projects is vastly different, `somesy` provides a very general solution to this problem
with the `fill` command. It takes a
[Jinja2](https://jinja.palletsprojects.com/en/3.1.x/)
template and returns the resulting file where the project metadata is inserted the form dictated by the template.

For example, a template is used to generate the
[`AUTHORS.md`](https://github.com/Materials-Data-Science-and-Informatics/somesy/blob/main/AUTHORS.md)
file in the somesy repository, which is also shown as the
[Credits](./credits.md) page, using the following command:

```shell
somesy fill docs/_template_authors.md -o AUTHORS.md
```

??? example "_template_authors.md"
    ```
    --8<-- "docs/_template_authors.md"
    ```

??? example "AUTHORS.md"
    ```
    --8<-- "AUTHORS.md"
    ```

The template gets the complete
[ProjectMetadata](reference/somesy/core/models.md#somesy.core.models.ProjectMetadata) as its context, so it is possible to access all included project and contributor information.

## FAQ

### Somesy introduces it's own metadata format... isn't this counter-productive?

We don't propose to use `somesy` as a new "standard". On the contrary, the whole
point of `somesy` is to help maintaining standard-compliant metadata alongside
other representations. To do its job, `somesy` needs to introduce a canonical
format to express the metadata it tries to manage for you, because otherwise
building such a tool is practically impossible.
Should you after some time decide you do not want to use it anymore, nothing is
lost - you keep all your `CITATION.cff` and `codemeta.json` and `pyproject.toml`
files and can continue to maintain them however you see fit.

The `somesy`-specific format is just the nice and convenient interface to make
everybody's life easier. Furthermore, nobody needs to care whether, under the
hood, you use `somesy` (or anything like it) or not - they can use the
corresponding files they already know to get the information they need.
So there is no "risk" involved in adopting `somesy`, because it does not try to
abolish any other formats or standards or becoming such.

### In my project, the effective authors and the publication authors are not the same! What to do?

The `author` flag in `somesy` is intended to mark people who significantly contributed
to the project in a hands-on way and are closely familiar with details, i.e. can answer
specific questions. A reason to stick with this strict understanding of "author"
is that a user will be usually interested in contacting such a person to help
them with problems.

However, we are aware that acknowledgement practices in different scientific
communities vary and current practices in academic publication do not allow for
sufficiently granular distinction of contributor roles.
Even though the proper solution to problem would be improving community practices,
`somesy` supports the `publication_author` flag, that can be set independently of the
`author` flag and will make sure that certain contributors **will** appear as authors
in an academic citation context (i.e. reflected in the `CITATION.cff` file, which can be
used for [Zenodo publications](https://docs.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html)), but **will not** appear as authors in a technical context
(such as the metadata in a software registry like [PyPI](https://pypi.org)).
