# somesy — Code Review Report

Date: 2026-11-03 · Commit: `716a040` (main) · Scope: `src/somesy/**`, `.pre-commit-hooks.yaml`

## How this was produced

- 5 parallel review agents (core/merge/harvest, pyproject/cff/npm/julia/fortran, pom/rust/mkdocs/git, codemeta, cli/commands) + 1 agent running repo-native checks.
- Agents wrote small repro scripts outside the repo (not included here).
- **Verification column**: `✔` = re-checked in main thread (code read and/or repro re-run); `R` = agent repro only; `C` = agent code-read only. Treat `C` items as "likely, confirm before fixing".

## 1. Tooling baseline

| Check | Result |
|---|---|
| pytest | 359 passed, 0 failed; coverage 90 % |
| Lowest coverage | `cli/fill.py` 44 %, `commands/init_config.py` 47 %, `cli/init.py` 63 %, `core/core.py` 77 %, `julia/writer.py` 77 %, `rust/writer.py` 78 %, `codemeta/writer.py` 80 %, `pyproject/models.py` 81 % |
| ruff check / format (v0.16.6, as pinned) | clean |
| pyright 1.1.411 | 0 errors |
| mypy 2.3.1 | 9 errors — meaningful: `commands/sync.py:181` (dict[str, bool\|None] → SomesyConfig), `package_json/writer.py:143` (HttpUrl → str, a real bug, see B6); rest are missing stubs (defusedxml, pyld, cffconvert) |
| Warnings | ~640 × `PydanticDeprecatedSince211`: `self.model_fields` on instance at `core/models.py:113,126` (removed in Pydantic v3) |
| Env drift | poetry venv has ruff 0.15.1, pre-commit pins 0.16.6 |
| Generated dirs (`coverage.xml`, `htmlcov`, `site`, `dist`, `scratch`, `.scannerwork`) | all git-ignored — fine |

Note: mypy runs in pre-commit but reports 9 errors on main — either CI does not run it on all files, or it is configured with narrower scope. Worth checking.

## 2. Cross-cutting patterns (fix once, fixes many)

1. **`HttpUrl` objects leak into serializers.** `Entity.website` is passed unconverted to JSON/XML writers → crash. Hits package.json (B6), pom.xml (B5), and is exactly the mypy error. Fix: `str(person.website)` in each `_from_person`, or a model serializer.
2. **Contributors computed from `metadata.people` instead of `metadata.contributors()`.** Authors get duplicated into contributors and entity contributors are dropped. Hits package.json (B12) and pom.xml (B11).
3. **Inconsistent "absent value" semantics in `core/writer.py:296-322` `sync`.** `homepage`/`repository`/`documentation` are set to `None` (deleting the key), while `version`/`keywords` are kept when absent. Consequences: Homepage removed from pyproject (B15), empty `<scm>`/`<site>` elements and lost `<connection>` in pom (B13), Julia deleting `version` (B9, which bypasses the guard). Decide one rule and apply it everywhere.
4. **Only `licenses[0]` written** for list licenses (`core/writer.py:313-316`, CFF) — silent data loss; PEP 621 writes `MIT OR Apache-2.0`.
5. **Duplicated person-parsing (`_to_person` try-Person-then-Entity)** in pyproject (×2), julia, fortran, rust, mkdocs; duplicated inline-table save loop in julia/fortran/pyproject; duplicated validators in `PoetryConfig`/`Pep621Config`. A shared helper would also have prevented B7/B8 (same bug copied).
6. **Global `json.dump` monkeypatch** (`json_wrapper.py:21`) — importing somesy changes `json.dump` process-wide (indent=2, ensure_ascii=False, trailing newline); codemeta's pretty-printing silently depends on `package_json/writer.py` having been imported. Replace with an explicit helper.
7. **Files opened without `encoding="utf-8"`** in `core/core.py:83,92,103,118`, `codemeta/writer.py:89`, `codemeta/enrich.py:100,162,173,196` → breaks on non-UTF-8 locales (Windows) with names like "Müller".
8. **Sync target list repeated ~5×** (`commands/sync.py:169-177, 197-292`, `cli/sync.py:176-237`, `cli/init.py`). A single table of target specs (writer, file attr, no_sync attr) would remove ~150 lines and the class of bugs like B1.

## 3. Bugs

### High

| # | Location | Defect / scenario | Ver. |
|---|---|---|---|
| B1 | `cli/init.py:195` | Interactive `somesy init config` writes `sync_package_json` (not a field; real one is `no_sync_package_json`, inverted). Every later run fails with `extra_forbidden`. Fix: `options["no_sync_package_json"] = not typer.confirm(...)` | ✔ |
| B2 | `commands/sync.py:181` | Monorepo packages: package's own `[config]` replaced wholesale by root CLI options. `no_sync_cff = true` in `pkg/somesy.toml` ignored → CITATION.cff still created. | ✔ |
| B3 | `cli/sync.py:166` | `--packages/-k` uses `existing_file_arg_config` (dir_okay=False) but packages are directories → `somesy sync -k pkg` exits 2. Option is unusable from CLI. | ✔ |
| B4 | `codemeta/enrich.py:125-126` | Poetry multi-constraint dep (`foo = [{version=..., python=...}, ...]`) → `AttributeError: 'Array' object has no attribute 'get'`; `enrich` is unguarded, so the whole `somesy sync` aborts. | ✔ |
| B5 | `pom_xml/writer.py:98-100` | Entity with `website` → `TypeError: HttpUrl is not JSON-like primitive` on sync. | ✔ |
| B6 | `package_json/writer.py:141-143` | Same as B5 for package.json → `TypeError: Object of type HttpUrl is not JSON serializable` on save. | ✔ (mypy) |
| B7 | `fortran/writer.py:100-116` | `save()` mutates `self._data` while iterating; `[[executable]]` in fpm.toml → `RuntimeError: dictionary keys changed during iteration`. Very common fpm layout. | ✔ |
| B8 | `julia/writer.py:64-80` | Same as B7 for Project.toml with any array-of-tables. | ✔ |
| B9 | `julia/writer.py:109` | `self.version = metadata.version` unguarded → no version in input deletes `version` from Project.toml. | ✔ |
| B10 | `harvest.py:40` | Only FileNotFound/Key/Type/ValueError caught; malformed pom.xml (`ParseError`) or mkdocs.yml (ruamel `ParserError`) aborts harvest instead of warning. | ✔ (code) |
| B11 | `pom_xml/writer.py:255` | Contributors synced from `metadata.people` → authors duplicated into `<contributors>`, entity contributors dropped. | R |
| B12 | `package_json/writer.py:189` | Same as B11 for package.json `contributors`. | R |
| B13 | `pom_xml/writer.py:224-241` | Absent repository/documentation → empty `<scm><url/></scm>` / `<site>` written; replacing `<scm>` drops `<connection>`/`<developerConnection>`; absent homepage removes `<url>`. | R |
| B14 | `codemeta/writer.py:227-279` | Contributor without ORCID gets `@id: urn:uuid:…`; reading back maps it into `orcid` → ValidationError; Role dicts mixed into person arrays break parsing. Merge-mode round trip fails. | R |
| B15 | `core/writer.py:318-322` | Absent homepage/repository/documentation → key deleted from target (e.g. pyproject `[project.urls] Homepage` removed, Changelog kept). See pattern 3. | R |
| B16 | `core/models.py` `Entity.same_person` (~L490-513) | Falls back to name equality even when both RORs (or websites) differ → two distinct orgs with the same name merged into one. `Person.same_person` handles ORCID mismatch correctly. | ✔ |
| B17 | `git/harvest.py:32-41` | `_remote` returns remote URL including credentials (`https://oauth2:SECRET@host/...`) → token can be written into metadata files. **Security-relevant.** Strip userinfo. | ✔ |

### Medium

| # | Location | Defect / scenario | Ver. |
|---|---|---|---|
| B18 | `core/models.py:101` `_reorder_dict` | Unordered keys appended from a `set` → order varies with `PYTHONHASHSEED` → noisy diffs in outputs. Use `[k for k in dct if k not in key_order]`. | ✔ |
| B19 | `merge.py:44-45` | `ssh://git@host:org/repo` → invalid `https://host:org/...`; `ssh://git@host:22/org/repo` keeps SSH port in https URL. | ✔ |
| B20 | `core/models.py:515-524` `Entity.model_dump_json` | `rorid` kept when website already set (docstring says removed); `json.dumps` without `ensure_ascii=False` → `Jülich`. | ✔ |
| B21 | `core/models.py:604-617` `Person.from_name_email_string` | Single-word name → `given-names=""` violates min_length → git author silently dropped. | R |
| B22 | `core/writer.py:350` / `models.py:78` | `model_copy(update=...)` skips `author_implies_publication` validator → harvested authors have `publication_author=None`. | R |
| B23 | `codemeta/writer.py:54-57` | `authors` getter reads `publication_authors` key that never exists → `harvest_metadata()` never returns codemeta authors. | R |
| B24 | `codemeta/writer.py:314-315` | DOI removed from input → old `identifier` DOI stays in codemeta.json (merge mode). | ✔ |
| B25 | `codemeta/enrich.py:233-240` | `.//dependency` also matches `<dependencyManagement>`; unresolved `${junit.version}` copied as version. | ✔ |
| B26 | `fortran/writer.py:42-51` | fpm.toml without `author` → `TypeError` in `harvest_metadata()` (`except ValueError` never fires). | ✔ |
| B27 | `package_json/models.py:120-131` | Valid npm maintainer without email (`{"name": "Jane"}`) dropped with "Invalid email" warning. | ✔ |
| B28 | `package_json/writer.py:150-181` | Valid npm entity contributor `{"name":"ACME","url":...}` → Entity built with `orcid=` → ValidationError on read. | R |
| B29 | `pyproject/models.py:112-115` | `PoetryConfig.license` has no default → Poetry-2 style (`[project]` + `[tool.poetry]`) without license fails validation. | R |
| B30 | `pom_xml/writer.py:119-138` | Single `<role>` parsed as str not list → ValidationError on read. | R |
| B31 | `pom_xml/writer.py:112` | Person vs Entity decided by "name contains a space" → `Helmholtz Association` round-trips to a Person. | R |
| B32 | `pom_xml/writer.py:157-161` | `authors` returns `[None]` when no `<developers>` → treated as non-empty. | R |
| B33 | `rust/writer.py:85-121` | Overwrites workspace inheritance (`version.workspace = true`) with literal values. Common in Cargo workspaces. | R |
| B34 | `mkdocs/writer.py:128-129` | `self.repo_name = …` sets a Python attr, never written to YAML (dead/ineffective). | ✔ |
| B35 | `mkdocs/models.py:18-21` | `site_name` validated with package-name regex → `site_name: My Docs` fails to load. | ✔ |
| B36 | `mkdocs/writer.py:72-73` | `site_description:` (null) → `TypeError` on save. | ✔ |
| B37 | `git/harvest.py:21` | Missing git raises `RuntimeError`, callers catch only `CalledProcessError/FileNotFoundError` → crash instead of `None`. | ✔ |
| B38 | `git/harvest.py:24-55` | Non-UTF-8 author bytes in git log → uncaught `UnicodeDecodeError`. | ✔ |
| B39 | `cli/util.py:75` + `core/core.py:39-46` | Explicit `-i nope/somesy.toml` silently falls back to discovered `.somesy.toml` (only logged at VERBOSE). | R |
| B40 | `cli/set_value.py:15` | `set` defaults to `somesy.toml`, doesn't use `discover_input` → unusable with `.somesy.toml`. | R |
| B41 | `cli/init.py:156` | All prompts asked before checking output exists → user answers 6 prompts then gets "already exists". | R |
| B42 | `json_wrapper.py:21` | Global monkeypatch; see pattern 6. | ✔ |

### Low

| # | Location | Defect | Ver. |
|---|---|---|---|
| B43 | `.pre-commit-hooks.yaml:7` | `files` regex has `cargo\.toml` (lowercase) — hook doesn't fire on `Cargo.toml`; `pom.xml`, `mkdocs.yml`, `codemeta.json`/`CITATION.cff` not listed either; `^`/`$` only anchor first/last alternative. | ✔ |
| B44 | `core/log.py:89-92` | `verbose_print` uses `message.format(args)` → KeyError on braces; unused → delete. | R |
| B45 | `core/models.py:820,851` | `_origin` not always set → `is_somesy_file()` AttributeError. Use `PrivateAttr(None)`. | R |
| B46 | `cli/util.py:59` | `wrap_exceptions` swallows click `Abort` → Ctrl-C/EOF prints empty "Error:". | R |
| B47 | `cli/set_value.py` | Invalid values print raw multi-error pydantic dumps (full SPDX list). | R |
| B48 | `cli/init.py:215` | `if fortran_file is not None or fortran_file != ""` always true. | C |
| B49 | `codemeta/utils.py:76-79` | Unknown-term check is top-level only. | R |
| B50 | `codemeta/enrich.py:156-167` | Lock file with multiple versions of a package → last wins silently. | C |
| B51 | `codemeta/writer.py:105-107` | Both `contIntegration` and `continuousIntegration` → old dropped silently. | R |
| B52 | `pyproject/models.py:153-188` | Email "warn, don't raise" branch unreachable; docstring wrong. | R |
| B53 | `pom_xml/writer.py:132` | Developer without `<name>` → KeyError. | C |
| B54 | `pom_xml/xmlproxy.py:242-250` | Children created with unqualified tags → `get()` on freshly set nodes fails (file output OK). | R |
| B55 | `git/harvest.py:83` | `path: Path = Path.cwd()` default evaluated at import time. | C |
| B56 | `pyproject/writer.py:311-325` | `Poetry.sync` monkeypatches `self._from_person`, restored only on success (use try/finally). | C |

## 4. Code-quality / dead code

- `src/somesy/codemeta/enhance/` — only `__pycache__`, no source → delete.
- `commands/sync.py:163` — unreachable `if config_file is None: continue`.
- `commands/sync.py:287` / `enrich.py:86-96` — `"mkdocs"` codemeta source passed but never handled.
- `main.py:17-18` — `@app.callback()` on `version` is overwritten by `common`'s callback (no-op).
- `core/writer.py:52` — docstring says `create_if_not_exists` defaults True; it's False. `only_first` (L115-154) never used with True.
- `cff/writer.py:80-81` — unreachable `elif self.description` branch.
- `pyproject/models.py:190-199, 281-293` — `validate_readme` validators lack `return v` and disagree (warn vs raise).
- `pyproject/writer.py:257-277` — `_poetry_version` stored vs branch condition inconsistent.
- `codemeta/writer.py:19` vs `utils.py:12` — `V3_CONTEXT` defined twice; `softwareHelp→url` rule duplicated (L160 and L323).
- `codemeta/writer.py:109-124` — full JSON-LD expansion run and discarded when not merging; redundant deepcopy/restore.
- `codemeta/enrich.py:221-222` — `getroot()` never None.
- `merge.py:78-91` — `same_person/same_entity` wrappers redundant; `writer.py:327-336` duplicates `merge._SCALAR_FIELDS`; `ensure_distinct_*` validators near-identical.
- `rust/writer.py:52-53`, `mkdocs/writer.py:59-60` — redundant `pass_validation` check.
- `pom_xml/writer.py:243-255` — re-sets license already set by `super().sync()`.
- `core/models.py:113,126` — replace `self.model_fields` with `type(self).model_fields` (Pydantic 2.11 deprecation).

## 5. Suggested order of work

1. **Quick, high-value fixes** (each a few lines, all with clear repros): B1, B3, B5/B6 (`str(website)`), B7/B8, B9, B17 (credential leak), B18, B43, B26, B36, Pydantic deprecation.
2. **Semantics decisions needed from maintainers** before fixing: absent-value rule (pattern 3 → B13, B15), multi-license output (pattern 4), monorepo config merge (B2), pom Person/Entity mapping (B31), Cargo workspace inheritance (B33).
3. **Refactors**: shared `_to_person` helper (pattern 5), sync target table (pattern 8), remove `json_wrapper` monkeypatch (pattern 6), utf-8 everywhere (pattern 7).
4. **Tests**: add regression tests for each fixed bug; raise coverage of `cli/fill.py`, `commands/init_config.py`, `cli/init.py` (where B1/B41/B48 live).

