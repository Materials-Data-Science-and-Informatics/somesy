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
    for fld in m.__fields__.values():
        n = fld.name

        t = fld.type_.__name__
        if t == "ConstrainedStrValue":
            t = "str"
        if t == "AnyUrl":
            t = "URL"
        if fld.field_info.min_items:
            t = f"list[{t}]"

        r = "**yes**" if fld.required else "no"
        v = json.dumps(fld.default, default=str) if fld.default is not None else ""
        d = fmt_desc(fld.field_info.description)
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
some of the currently supported formats.

=== "Person Metadata"
    | Field Name       | Poetry Config | SetupTools Config | CITATION.cff    | Requirement |
    | ---------------- | ------------- | ----------------- | --------------- | ----------- |
    | given-names      | name+email    | name              | given-names     | required    |
    | family-names     | name+email    | name              | family-names    | required    |
    | email            | name+email    | email             | email           | required    |
    | orcid            | -             | -                 | orcid           | optional    |
    | *(many others)*  | -             | -                 | *(same)*        | optional    |

=== "Project Metadata"
    | Field Name        | Poetry Config | SetupTools Config | CITATION.cff    | Requirement |
    | ----------------- | ------------- | ----------------- | --------------- | ----------- |
    | name              | name          | name              | title           | required    |
    | description       | description   | description       | abstract        | required    |
    | license           | license       | license           | license         | required    |
    | version           | version       | version           | version         | optional    |
    |                   |               |                   |                 |             |
    | *author=true*     | authors       | authors           | authors         | required    |
    | *maintainer=true* | maintainers   | maintainers       | contact         | optional    |
    |                   |               |                   |                 |             |
    | keywords          | keywords      | keywords          | keywords        | optional    |
    | repository        | repository    | urls.repository   | repository_code | optional    |
    | homepage          | homepage      | urls.homepage     | url             | optional    |

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

which is located in the current working directory. If you want to provide
the somesy input file from a different location, you can pass it with the `-i` option.

### Synchronization

Unless configured otherwise, `somesy` will create `CITATION.cff`
and `codemeta.json` files if they do not exist.
Other supported files (such as `pyproject.toml`) are updated if they already
exist in your repository.

If you do not want that somesy creates/synchronizes these files,
you can disable them by CLI options or in your somesy configuration.

### Somesy input file

In the [quickstart](./quickstart.md) you can find an example somesy input file.

All possible metadata fields and configuration options are explained further [above](#schemas-overview).

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

### Codemeta

While `somesy` is modifying existing files for most supported formats,
[CodeMeta](https://codemeta.github.io/) is implemented differently.

In order to avoid redundant work, `somesy` relies on existing tools to generate
`codemeta.json` files. So when you synchronize the metadata and the codemeta
target is enabled, `somesy` will generate your `codemeta.json` by:

* synchronizing metadata to a `pyproject.toml` or `package.json` (if enabled)
* synchronizing metadata to a `CITATION.cff` (if enabled)
* running `cffconvert` and `codemetapy` to combine both sources into a final `codemeta.json`

!!! warning
    The `codemeta.json` is overwritten and regenerated from scratch every time you `sync`,
    so **do not edit it** if you have the codemeta target enabled in `somesy`!

As `codemeta.json` is considered a technical "backend-format" derived from other
inputs, in most cases you probably do not need or should edit it by hand anyway.

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