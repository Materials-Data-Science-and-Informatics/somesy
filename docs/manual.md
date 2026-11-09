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

    Detailed contribution information is synchronized to `codemeta.json` as
    CodeMeta roles. Other output formats may not support it.

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

    | Somesy Field     | Poetry Config | PEP 621 `[project]` | Java POM     | Julia Config | Fortran Config | package.json | mkdocs.yml | Rust Config    | CITATION.cff    | CodeMeta       |
    | ---------------- | ------------- | ----------------- | ------------ | ------------ | -------------- | ------------ | ---------- | -------------- | --------------- | -------------- |
    |                  |               |                   |              |              |                |              |            |                |                 |                |
    | **given-names**  | name(+email)    | name              | name         | name(+email)   | name(+email)     | name         | name(+email) | name(+email)     | givenName       | name(+email)     |
    | **family-names** | name(+email)    | name              | name         | name(+email)   | name(+email)     | name         | name(+email) | name(+email)     | familyName      | name(+email)     |
    | email            | name(+email)    | email             | email        | name(+email)   | name(+email)     | email        | name(+email) | name(+email)     | email           | name(+email)     |
    | orcid            | -             | -                 | url          | -            | -              | url          | -          | -              | id              | -              |
    | *(many others)*  | -             | -                 | -            | -            | -              | -            | -          | -              | *(same)*        | -              |

=== "Entity Metadata"

    | Somesy Field     | Poetry Config | PEP 621 `[project]` | Java POM     | Julia Config | Fortran Config | package.json | mkdocs.yml | Rust Config    | CITATION.cff    | CodeMeta       |
    | ---------------- | ------------- | ----------------- | ------------ | ------------ | -------------- | ------------ | ---------- | -------------- | --------------- | -------------- |
    |                  |               |                   |              |              |                |              |            |                |                 |                |
    | **name**  | name(+email)    | name              | name         | name(+email)   | name(+email)     | name         | name(+email) | name(+email)     | givenName       | name(+email)     |
    | email     | name(+email)    | email             | email        | name(+email)   | name(+email)     | email        | name(+email) | name(+email)     | email           | name(+email)     |
    | rorid   | -             | -                 | url          | -            | -              | url          | -          | -              | - *(never written)* | -              |
    | website   | -             | -                 | url          | -            | -              | url          | -          | -              | id              | -              |
    | *(many others)*  | -             | -                 | -            | -            | -              | -            | -          | -              | *(same)*        | -              |

=== "Project Metadata"

    | Somesy Field      | Poetry Config | PEP 621 `[project]`  | Java POM                        | Julia Config | Fortran Config | package.json | mkdocs.yml       | Rust Config     | CITATION.cff    | CodeMeta          |
    | ----------------- | ------------- | ------------------ | ------------------------------- | ------------ | -------------- | ------------ | ---------------- | --------------- | --------------- | ----------------- |
    |                   |               |                    |                                 |              |                |              |                  |                 |                 |                   |
    | **name**          | name          | name               | name                            | name         | name           | name         | site_name        | name            | title           | name              |
    | **description**   | description   | description        | description                     | -            | description    | description  | site_description | description     | abstract        | description       |
    | abstract          | -             | -                  | -                               | -            | -              | -            | -                | -               | abstract        | -                 |
    | doi               | -             | -                  | -                               | -            | -              | -            | -                | -               | doi             | identifier        |
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

If several `license` values are given, all of them are written: as a list in
`CITATION.cff` and `codemeta.json`, as one `<license>` element each in
`pom.xml`, and as an SPDX `A OR B` expression in `pyproject.toml`,
`package.json`, `Cargo.toml` and `fpm.toml`.

If the somesy input has no `homepage`, `repository` or `documentation`, URLs
already present in an output file are kept, not deleted.

In `pom.xml`, free-text `<role>` values are kept; somesy only manages roles
that are somesy contribution types. In `mkdocs.yml`, `repo_name` is written as
`org/repo` only when it is not already set, and `site_name` may be free text.
`Cargo.toml` workspace inheritance (e.g. `version.workspace = true`) is kept
and such values are ignored when harvesting. As in Cargo, `authors` and
`version` are optional in an existing `Cargo.toml`.

`package.json` and `fpm.toml` have a single author slot, so only the first
author is written there. In `package.json`, further authors are listed first in
`contributors`, followed by the other contributors, and maintainers are written
as a list.

#### People in output files

Existing people in an output file are matched with the people from the somesy
input by identity: ORCID first, then email, then name. If one person matches
several existing entries, somesy logs a warning and uses the entry with the same
ORCID (otherwise the first one). The somesy input is the source of truth for the
managed person fields: a field that was removed from the input (for example an
email) is also cleared in the outputs. The role and contribution flags
(`author`, `maintainer`, `publication_author` and the contribution fields) are
not touched by this. Existing entries that somesy cannot parse are kept
untouched, and incomplete people in `CITATION.cff` (missing a required field)
are kept with a warning.

Note that the mapping is often not 1-to-1. For example, CITATION.cff allows rich
specification of author contact information and complex names. In contrast,
poetry only supports a simple string with a name and email (like in git commits)
to list authors and maintainers. **Therefore somesy sometimes must do much more
than just move or rename fields**. This means that giving a clean and complete
mapping overview is not feasible. In case of doubt or confusion, please open an
issue or consult the `somesy` code.

### Description and abstract

The `description` is a short, one-line summary of the project. For Python
packages it becomes the package summary, which PyPI only accepts as a single
line of at most 512 characters; somesy warns when the `description` synced into
`pyproject.toml` breaks either rule.

For a longer text, such as a multi-paragraph abstract for citations, set the
optional `abstract` field. It is only written to `CITATION.cff` (as `abstract`);
all other files keep the short `description`. Without an `abstract`,
`CITATION.cff` uses the `description` instead.

```toml
[project]
description = "Brief description of my amazing software."
abstract = """
A longer abstract of my amazing software.

It can span several paragraphs.
"""
```

### CodeMeta Enrichment

When writing `codemeta.json`, Somesy first synchronizes the canonical metadata
from `somesy.toml`. It then fills **missing** CodeMeta fields from enabled,
configured language files and Git. This preserves the source priority:

```text
somesy.toml > language file > Git history
```

In merge mode, the enriched keys (`readme`, `issueTracker`, `releaseNotes`,
`softwareRequirements`, `programmingLanguage`, `runtimePlatform`,
`codeRepository`, `dateCreated`, `dateModified` and `version`) are refreshed on
every sync; old values are only kept if nothing provides a new one. A repeated
`somesy sync --merge` does not rewrite an unchanged `codemeta.json`. Legacy
CodeMeta files are upgraded on disk, and an output file that is missing on disk
is always written.

`dateModified` is set to the current date (UTC) whenever the content of
`codemeta.json` changes. A new commit or tag alone does not change the file: if
nothing else changed, the previous `dateModified` and a `version` taken from a
Git tag are kept. So a sync on committed files, such as
`pre-commit run --all-files` in CI, leaves `codemeta.json` unchanged. A new tag
is picked up the next time the metadata changes; a `version` set in
`somesy.toml` or a language file is always used.

The enrichment never replaces a CodeMeta field written from canonical Somesy
metadata. When `merge_codemeta` is enabled, unrelated user-managed CodeMeta
fields remain unchanged as well.

| Source | Enriched CodeMeta fields |
| --- | --- |
| `pyproject.toml`, lock file (`uv.lock`, `poetry.lock` or `pdm.lock`) | Python runtime, direct dependencies, README URL, issue tracker, release notes |
| `package.json` | JavaScript or TypeScript (when a `tsconfig*.json` is next to it), Node.js runtime, runtime/peer/optional dependencies, issue tracker |
| `Cargo.toml`, `Project.toml`, `fpm.toml`, `pom.xml` | Programming language, runtime version where declared, dependencies |
| Git | Repository, issue tracker for GitHub/GitLab remotes, nearest tag version, first commit date |

Development and test dependencies are not included; neither PEP 735
`[dependency-groups]` nor `[project.optional-dependencies]` extras are treated
as project requirements. A lock file only provides exact versions for
dependencies declared by the project; transitive lock-file entries are not
emitted. The nearest lock file at or above the `pyproject.toml` is used, so
workspace members that share a lock file at the workspace root are covered.
PyPI classifiers are kept in `pyproject.toml` because CodeMeta has no reliable
equivalent.

`[project.urls]` key names are not standardized by PEP 621. Common spellings
are recognized regardless of capitalization and separators: `Issues`,
`Issue Tracker`, `Bug Tracker`, `Bug Reports` and `Bugs` fill `issueTracker`,
while `Changelog`, `Changes`, `Release Notes` and `History` fill
`releaseNotes`. When syncing `homepage`, `repository` and `documentation` into
`[project.urls]`, somesy likewise updates an entry that already exists under a
different spelling instead of adding a second one.

The first commit date requires complete Git history. In a shallow clone, Somesy
omits `dateCreated` rather than reporting the shallow boundary as the project
creation date. For reproducible generated metadata in CI, configure a full
checkout (for GitHub Actions, `fetch-depth: 0`).

### PEP 621 `dynamic` fields

For `pyproject.toml` targets using the PEP 621 `[project]` table (uv, hatchling,
flit, PDM, setuptools) as well as for Poetry v2, somesy respects the
[PEP 621 `dynamic` field](https://peps.python.org/pep-0621/#dynamic). Every
field somesy syncs into `pyproject.toml` honours it: `version`, `description`,
`license`, `authors`, `maintainers`, `keywords` and `urls` (the homepage,
repository and documentation URLs). If such a field is listed in `dynamic`, the
value is provided at build time rather than written statically in the file. In
this case somesy will:

- **skip validation** of that field (`version` and `authors` are required in the
  file unless listed in `dynamic`; `description` is optional), and
- **not overwrite** the field during sync, logging a warning instead.

For example, if your `pyproject.toml` contains:

```toml
[project]
name = "my-package"
dynamic = ["version", "description"]
```

somesy will sync all other managed fields as usual but leave `version` and
`description` untouched, because they are expected to be set dynamically at
build time.

For the license, somesy only manages the SPDX expression. A `license = { text = ... }`
table is replaced by the SPDX expression, but `license = { file = ... }` and
`license-files` are left untouched, with a warning.

With Poetry 2 and both `[project]` and `[tool.poetry]` present, `[project]` is
updated. The legacy keys in `[tool.poetry]` (e.g. `version`, `authors`) are
updated only if they already exist there; missing ones are never added.

**people** and **entities** are mapped to authors/maintainers/contributors depending
on the output format. Both fields are marked as necessary but what `somesy` need is an
author either in **people** or **entities**.

When an **entity** has a `ror id` but no `website` set, url related fields will be
filled with the ROR URL (this is also the website in `CITATION.cff`, which never
contains a `rorid` key).

## The somesy CLI tool

You can see all supported somesy CLI command options using `somesy --help`:

```bash exec="true" source="above" result="ansi"
somesy sync --help
```

Everything that can be configured as a CLI flag can also be set in a `somesy.toml` file
in the `[config]` section. CLI arguments set in an input file override the
defaults, while options passed as CLI arguments override the configuration.
Only flags that are given explicitly override the configuration: for example,
`--overwrite` overrides `merge_codemeta = true` from the config file, and
`--no-pass-validation` overrides `pass_validation = true`.
The `-P` shortcut disables pyproject synchronization, while `-V`
(`--pass-validation/--no-pass-validation`) passes output validation.

If several of `--info`, `--verbose` and `--debug` are given, somesy shows a
warning and the most verbose one wins. The `somesy` logger propagates to the root
logger, so when somesy is used as a library, its log records reach your own
logging configuration.

Output files are created only when they are saved, so a failed sync does not
leave new empty files behind. Missing output folders are created. Saves are
atomic (a temporary file is renamed over the target, and the file mode is
kept). If the target cannot be replaced, for example because another program
has it open on Windows, somesy writes it directly and shows a warning. A sync is
also two-phase: all targets (including those of packages) are prepared first
and written only if all of them succeed. If writing a file fails, the files
already written are restored and new files are removed.

Clear errors are raised for a `Cargo.toml` without a `[package]` table (e.g. a
workspace root) and for an empty `mkdocs.yml`. An empty or comment-only
`CITATION.cff` is treated like a new file. In `pom.xml`, existing entities are
matched by name and XML comments are preserved.

Synchronization only writes a target when its parsed metadata changes. Formatter
choices such as indentation, wrapping, quotes, comments, and mapping-key order are
therefore preserved; list order and scalar values remain significant.

### Initialize a project

Use `somesy init` to create a standalone `somesy.toml` from an existing project:

```bash
somesy init
```

Initialization reads metadata from all supported project files present in the
current directory and harvests project information and authors from Git history.
The harvested values are merged into Somesy’s general metadata model before the
file is written.

Only missing required values are requested interactively:

- project name
- project description
- SPDX license
- one author, as either a person or an entity

For a person, the command asks for given names, family names, and optionally an
email address. For an entity, it asks for the organization name and optionally
an email address. Git authors count as project authors; therefore, the author
prompt is shown only when no author was found in the harvested metadata.

For scripts, use `somesy init --non-interactive`. It never prompts, warns about
any missing required values, and writes the harvested metadata. To synchronize
an incomplete file, explicitly use `somesy sync --pass-validation` or set
`pass_validation = true` in the config; missing values are omitted from output.

Only the history of the current `HEAD` is used to find Git authors, not that of
all branches. Git bot accounts (names ending in `[bot]`) are skipped. Git authors with a
single-word name are not added, with a warning; add them manually.

Detected project files are enabled as synchronization targets. Targets that are
not present are disabled in the generated `[config]` section. The generated file
is not overwritten by default (somesy fails before prompting if it exists):

```bash
somesy init --output-file path/to/somesy.toml
somesy init --overwrite
```

Use `somesy init config` when you want to configure synchronization options
manually instead of deriving them from the files in the project. It merges the
answers into the `[config]` section of the existing input file, keeping other
keys, and creates a `somesy.toml` if no input file exists.

### Update project metadata

Use `somesy set` to update one scalar project-metadata value in an existing
`somesy.toml` file:

```bash
somesy set version 1.2.3
```

The command supports `name`, `description`, `abstract`, `version`, `license`,
`homepage`, `repository`, and `documentation`. It does not update structured values such as
keywords, people, or entities. It gives a clear error if the file has no
`[project]` table.

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
If the file passed with `-i` does not exist, somesy logs a warning and falls back to
this discovery, naming the file it uses instead (this is not an error). Candidate
files that are malformed are skipped during discovery. `somesy set` uses the same discovery when `-i` is not given.

### Somesy Input File

Here is an example how project metadata and `somesy` can be configured using
one of the supported input formats:

=== "somesy.toml"

    --8<-- "README.md:somesytoml"

=== "pyproject.toml"

    ```toml
    [project] # or [tool.poetry] in case of poetry version 1
    name = "my-amazing-project"
    version = "0.1.0"
    ...

    [tool.somesy.project]
    name = "my-amazing-project"
    version = "0.1.0"
    description = "Brief description of my amazing software."

    keywords = ["some", "descriptive", "keywords"]
    license = ["MIT", "Apache-2.0"]
    repository = "https://github.com/username/my-amazing-project"

    # Multiple licenses are supported; single-value targets use the first one.

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

    Each output file, such as package.json file, have its required fields and these fields are enforced by `somesy`. However, in case of mono-repos or multi-package repositories, some of the fields could be omitted, such as `version`. For `pyproject.toml` files, the preferred solution is to list those fields under `dynamic` (e.g. `dynamic = ["version"]`) — somesy will then skip validation and sync for those fields. For other formats, or as a last resort, you can set `pass_validation` to `true` in the somesy config to bypass validation entirely. `somesy` will fail otherwise. This applies to all synced `pyproject.toml` fields that support `dynamic` (see above).

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

`packages` (or `--packages/-k` on the command line) takes directories. A package's own `cff_file` and `codemeta_file` settings are honoured (relative to the package directory). Packages that fail to load are skipped with a warning, and a summary lists them at the end. Each package's own `[config]` is the base; only options explicitly passed on the root command line override it. Values from the root config file are not inherited.

Each of these packages (sub-folders) are assumed to have separate somesy metadata in the folder. These packages could be a `somesy` supported language/framework or it could be any other language. `somesy` will create at least `CITATION.CFF` and `codemeta.json` regardless if not instructed otherwise.
