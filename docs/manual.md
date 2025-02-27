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
from somesy.core.models import SomesyInput, ProjectMetadata, Person, SomesyConfig, Entity
from pydantic_core import PydanticUndefined
from typing_extensions import get_args

def format_type(t):
    # Handle List and Dict types
    if "list[" in str(t).lower():
        inner = get_args(t)[0]
        return f"List[{inner.__name__}]"
    if "dict[" in str(t).lower():
        key_type, val_type = get_args(t)
        return f"Dict[{key_type.__name__}, {val_type.__name__}]"
    return t.__name__

def pp_type(th):
    # Handle Union types by showing all possibilities
    args = get_args(th)
    if args:
        # Filter out None/NoneType if present (from Optional)
        types = [t for t in args if str(t) != "<class 'NoneType'>"]
        # Convert each type to its formatted name and join with ' / '
        return " / ".join(format_type(t) for t in types)
    # Handle non-Union types
    return format_type(th)

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
print(model2md(Entity).getvalue())
print(model2md(SomesyConfig).getvalue())
```

### Metadata Mapping

From its own schema `somesy` must convert the information into the target formats.
The following tables sketch how fields are mapped to corresponding other fields in
some of the currently supported formats. Bold field names are mandatory, the others are optional.

=== "Person Metadata"

    | Somesy Field     | Poetry Config | SetupTools Config | Java POM     | Julia Config | Fortran Config | package.json | mkdocs.yml | Rust Config    | CITATION.cff    | CodeMeta       |
    | ---------------- | ------------- | ----------------- | ------------ | ------------ | -------------- | ------------ | ---------- | -------------- | --------------- | -------------- |
    |                  |               |                   |              |              |                |              |            |                |                 |                |
    | **given-names**  | name(+email)    | name              | name         | name(+email)   | name(+email)     | name         | name(+email) | name(+email)     | givenName       | name(+email)     |
    | **family-names** | name(+email)    | name              | name         | name(+email)   | name(+email)     | name         | name(+email) | name(+email)     | familyName      | name(+email)     |
    | email            | name(+email)    | email             | email        | name(+email)   | name(+email)     | email        | name(+email) | name(+email)     | email           | name(+email)     |
    | orcid            | -             | -                 | url          | -            | -              | url          | -          | -              | id              | -              |
    | *(many others)*  | -             | -                 | -            | -            | -              | -            | -          | -              | *(same)*        | -              |

=== "Entity Metadata"

    | Somesy Field     | Poetry Config | SetupTools Config | Java POM     | Julia Config | Fortran Config | package.json | mkdocs.yml | Rust Config    | CITATION.cff    | CodeMeta       |
    | ---------------- | ------------- | ----------------- | ------------ | ------------ | -------------- | ------------ | ---------- | -------------- | --------------- | -------------- |
    |                  |               |                   |              |              |                |              |            |                |                 |                |
    | **name**  | name(+email)    | name              | name         | name(+email)   | name(+email)     | name         | name(+email) | name(+email)     | givenName       | name(+email)     |
    | email     | name(+email)    | email             | email        | name(+email)   | name(+email)     | email        | name(+email) | name(+email)     | email           | name(+email)     |
    | rorid   | -             | -                 | url          | -            | -              | url          | -          | -              | id              | -              |
    | website   | -             | -                 | url          | -            | -              | url          | -          | -              | id              | -              |
    | *(many others)*  | -             | -                 | -            | -            | -              | -            | -          | -              | *(same)*        | -              |

=== "Project Metadata"

    | Somesy Field      | Poetry Config | SetupTools Config  | Java POM                        | Julia Config | Fortran Config | package.json | mkdocs.yml       | Rust Config     | CITATION.cff    | CodeMeta          |
    | ----------------- | ------------- | ------------------ | ------------------------------- | ------------ | -------------- | ------------ | ---------------- | --------------- | --------------- | ----------------- |
    |                   |               |                    |                                 |              |                |              |                  |                 |                 |                   |
    | **name**          | name          | name               | name                            | name         | name           | name         | site_name        | name            | title           | name              |
    | **description**   | description   | description        | description                     | -            | description    | description  | site_description | description     | abstract        | description       |
    | **license**       | license       | license            | licenses.license                | -            | license        | license      | -                | license         | license         | license           |
    | version       | version       | version            | version                         | version      | version        | version      | -                | version         | version         | version           |
    |                   |               |                    |                                 |              |                |              |                  |                 |                 |                   |
    | ***author=true*** | authors       | authors            | developers                      | authors      | author         | author       | site_author      | authors         | authors         | author            |
    | *maintainer=true* | maintainers   | maintainers        | -                               | -            | maintainer     | maintainers  | -                | -               | contact         | maintainer        |
    | *people*          | -             | -                  | -                               | -            | -              | contributors | -                | -               | -               | contributor       |
    | *entities*          | -             | -                  | -                               | -            | -              | contributors | -                | -               | -               | contributor       |
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

**people** and **entities** are mapped to authors/maintainers/contributors depending
on the output format. Both fields are marked as necessary but what `somesy` need is an
author either in **people** or **entities**.

When an **entity** has a `ror id` but no `website` set, url related fields will be
filled with `ror id`.

## The somesy CLI tool

You can see all supported somesy CLI command options using `somesy --help`:

```bash exec="true" source="above" result="ansi"
somesy sync --help
```

Everything that can be configured as a CLI flag can also be set in a `somesy.toml` file
in the `[config]` section. CLI arguments set in an input file override the
defaults, while options passed as CLI arguments override the configuration.

Without an input file specifically provided, somesy will check if it can find a valid

-   `.somesy.toml`
-   `somesy.toml`
-   `pyproject.toml` (in `tool.somesy` section)
-   `Project.toml` (in `tool.somesy` section)
-   `fpm.toml` (in `tool.somesy` section)
-   `package.json` (in `somesy` section)
-   `Cargo.toml` (in `package.metadata.somesy` section)

which is located in the current working directory. If you want to provide
the somesy input file from a different location, you can pass it with the `-i` option.

### Somesy Input File

Here is an example how project metadata and `somesy` can be configured using
one of the supported input formats:

=== "somesy.toml"

    --8<-- "README.md:somesytoml"

=== "pyproject.toml"

    ```toml
    [tool.poetry] # [project] in case of poetry version 2
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

    # add an organization as a maintainer
    [[tool.somesy.project.entities]]
    name = "My Super Organization"
    email = "info@my-super-org.com"
    website = "https://my-super-org.com"
    rorid = "https://ror.org/02nv7yv05" # highly recommended set a ror id for your organization

    [tool.somesy.config]
    verbose = true     # show detailed information about what somesy is doing
    ```

### Support for mono-repos and multi-package projects

A research software project might have multiple packages in the root repository. These packages might be in the same or different software languages or frameworks. `somesy` currently supports synchronizing multiple output files from one somesy project metadata input.

#### Sync from one somesy input

This is the case where you have only one somesy metadata set in your root folder. Output files can be set in the somesy config section.

```toml
[project]
...

[config]
pass_validation = true
package_json_file = ['package.json', 'package1/package.json']
pyproject_toml_file = 'package2/pyproject.toml'
```

!!! warning

    Each output file, such as package.json file, have its required fields and these fields are enforced by `somesy`. However, in case of mono-repos or multi-package repositories, some of the fields could be omitted, such as `version`. Therefore, we suggest users to set `pass_validation` to `true` if this is the case. `somesy` will fail otherwise.

The example above shows a project with a `package.json` file in the root folder and 2 packages in it. Three files are set here so all of them will be updated according to ground truth of `somesy project metadata`.

!!! note

    Let's remember `somesy` will create a `CITATION.CFF` and `codemeta.json` file in the root folder if it is set otherwise either by cli or by config.

#### Packages (sub-modules) with their own somesy file

A project with multiple packages inside can have completely different metadata such version and authors. Therefore, each package should have a separate metadata, in other words, separate `somesy` config and project metadata.

```toml
[project]
...

[config]
packages = ['package1', 'package2', 'package3']
```

Each of these packages (sub-folders) are assumed to have separate somesy metadata in the folder. These packages could be a `somesy` supported language/framework or it could be any other language. `somesy` will create at least `CITATION.CFF` and `codemeta.json` regardless if not instructed otherwise.
