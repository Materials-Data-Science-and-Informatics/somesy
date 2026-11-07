"""Regression tests for config merging, CLI overrides and log-level state."""

import logging
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

import somesy.cli.sync as cli_sync
from somesy.cli.util import resolved_somesy_input
from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.core.models import PartialProjectMetadata, ProjectMetadata
from somesy.main import app

runner = CliRunner()
logger = logging.getLogger("somesy")

COMPLETE = """\
[project]
name = "demo"
version = "1.0.0"
description = "Demo project."
license = "MIT"

[[project.people]]
family-names = "Doe"
given-names = "John"
email = "john.doe@example.com"
author = true
maintainer = true
"""

INCOMPLETE = """\
[project]
name = "demo"
"""


def write_somesy(tmp_path: Path, project: str, config: str = "") -> Path:
    path = tmp_path / "somesy.toml"
    path.write_text(project + ("\n[config]\n" + config if config else ""))
    return path


# ---- 1a


def test_cli_false_overrides_config_true(tmp_path):
    path = write_somesy(
        tmp_path, COMPLETE, "merge_codemeta = true\npass_validation = true\n"
    )
    inp = resolved_somesy_input(
        input_file=path, merge_codemeta=False, pass_validation=False
    )
    assert inp.config.merge_codemeta is False
    assert inp.config.pass_validation is False


def test_config_file_value_kept_when_cli_not_passed(tmp_path):
    path = write_somesy(tmp_path, COMPLETE, "merge_codemeta = true\n")
    inp = resolved_somesy_input(input_file=path, merge_codemeta=None)
    assert inp.config.merge_codemeta is True


def test_cli_overrides_contain_exactly_explicit_options(tmp_path):
    path = write_somesy(tmp_path, COMPLETE, "pass_validation = true\n")
    inp = resolved_somesy_input(
        input_file=path,
        merge_codemeta=False,
        no_sync_cff=None,
        no_sync_pyproject=True,
        pass_validation=None,
    )
    ov = inp.config._cli_overrides
    assert ov["merge_codemeta"] is False
    assert ov["no_sync_pyproject"] is True
    assert "pass_validation" not in ov
    assert "no_sync_cff" not in ov


@pytest.fixture
def captured(monkeypatch):
    got = {}

    def fake(**kwargs):
        got.update(kwargs)
        raise SystemExit(0)

    monkeypatch.setattr(cli_sync, "resolved_somesy_input", fake)
    return got


def test_sync_cli_defaults_are_none(captured):
    runner.invoke(app, ["sync"])
    assert captured["merge_codemeta"] is None
    assert captured["pass_validation"] is None


def test_sync_cli_explicit_false_flags(captured):
    result = runner.invoke(app, ["sync", "--overwrite", "--no-pass-validation"])
    assert result.exit_code == 0, result.output
    assert captured["merge_codemeta"] is False
    assert captured["pass_validation"] is False


def test_sync_cli_positive_flags(captured):
    runner.invoke(app, ["sync", "--merge", "-V"])
    assert captured["merge_codemeta"] is True
    assert captured["pass_validation"] is True


# ---- 1e


def test_no_pass_validation_makes_project_strict(tmp_path):
    path = write_somesy(tmp_path, INCOMPLETE, "pass_validation = true\n")
    inp = resolved_somesy_input(input_file=path)
    assert isinstance(inp.project, PartialProjectMetadata)
    with pytest.raises(ValidationError):
        resolved_somesy_input(input_file=path, pass_validation=False)


def test_pass_validation_flag_allows_incomplete_file(tmp_path):
    path = write_somesy(tmp_path, INCOMPLETE)
    with pytest.raises(ValidationError):
        resolved_somesy_input(input_file=path)
    inp = resolved_somesy_input(input_file=path, pass_validation=True)
    assert isinstance(inp.project, PartialProjectMetadata)


def test_final_project_type_follows_merged_config(tmp_path):
    path = write_somesy(tmp_path, COMPLETE, "pass_validation = true\n")
    inp = resolved_somesy_input(input_file=path, pass_validation=False)
    assert type(inp.project) is ProjectMetadata


# ---- 1c


def _sync_args(path):
    return [
        "sync",
        "-i",
        str(path),
        "--no-sync-cff",
        "--no-sync-codemeta",
        "--no-sync-pyproject",
    ]


def test_log_level_not_inherited_between_invocations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = write_somesy(tmp_path, COMPLETE, "verbose = true\n")
    runner.invoke(app, ["-vvv", *_sync_args(path)])
    assert logger.getEffectiveLevel() == logging.DEBUG
    result = runner.invoke(app, _sync_args(path))
    assert result.exit_code == 0, result.output
    assert SomesyLogLevel.to_logging(SomesyLogLevel.VERBOSE) == (
        logger.getEffectiveLevel()
    )


def test_config_log_level_not_recorded_as_cli_level(tmp_path):
    from somesy.core.log import get_log_level, reset_log_level

    reset_log_level()
    path = write_somesy(tmp_path, COMPLETE, "debug = true\n")
    resolved_somesy_input(input_file=path)
    assert get_log_level() is None
    set_log_level(SomesyLogLevel.DEBUG)  # restore session state


def test_multiple_log_flags_use_most_verbose_and_warn(caplog):
    with caplog.at_level("WARNING", logger="somesy"):
        lv = SomesyLogLevel.from_flags(info=True, verbose=True)
    assert lv == SomesyLogLevel.VERBOSE
    assert any(r.levelname == "WARNING" for r in caplog.records)


def test_logger_propagation_deterministic():
    from somesy.core.log import init_log

    logger.propagate = False
    init_log()
    first = logger.propagate
    logger.propagate = not first
    init_log()
    assert logger.propagate == first
