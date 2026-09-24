import logging
import re

import pytest
import tomlkit
from typer.testing import CliRunner

from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.main import app

runner = CliRunner()
logger = logging.getLogger("somesy")


def test_dotted_package_name_syncs_and_converges(tmp_path, monkeypatch):
    """A dotted PEP 621 name embedded in [tool.somesy.project] syncs and converges."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# acme.widgets\n")
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """\
[project]
name = "acme.widgets"
version = "0.1.0"
description = "old description"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.somesy.project]
name = "acme.widgets"
version = "0.2.0"
description = "dotted name synced"
license = "MIT"

[[tool.somesy.project.people]]
given-names = "Jane"
family-names = "Doe"
email = "jane.doe@example.com"
author = true
maintainer = true
"""
    )
    sync_args = ["sync", "-i", "pyproject.toml", "--no-sync-cff", "--no-sync-codemeta"]
    before = tomlkit.parse(pyproject_path.read_text())

    result = runner.invoke(app, sync_args)
    assert result.exit_code == 0, result.output

    synced = tomlkit.parse(pyproject_path.read_text())
    assert synced["project"]["name"] == "acme.widgets"
    assert synced["project"]["version"] == "0.2.0"
    assert synced["project"]["description"] == "dotted name synced"
    assert synced["build-system"] == before["build-system"]
    assert synced["tool"]["somesy"] == before["tool"]["somesy"]
    assert not (tmp_path / "CITATION.cff").exists()
    assert not (tmp_path / "codemeta.json").exists()

    first_run = pyproject_path.read_bytes()

    result = runner.invoke(app, sync_args)
    assert result.exit_code == 0, result.output
    assert pyproject_path.read_bytes() == first_run


def test_app_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "somesy version: " in result.stdout


def test_sync_options_have_unique_shortcuts():
    result = runner.invoke(app, ["sync", "--help"])
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout)

    assert result.exit_code == 0
    assert "-P" in output and "--no-sync-pyproject" in output
    assert "-V" in output and "--pass-validation" in output
    assert "parameter -P is used more than once" not in result.output


@pytest.mark.parametrize("log_level", [lv for lv in SomesyLogLevel])
def test_log_levels(log_level):
    set_log_level(log_level)
    assert logger.getEffectiveLevel() == SomesyLogLevel.to_logging(log_level)

    # print stuff to see that rich is always enabled
    # but configured matching the log level
    print(f"testing log level {log_level}")
    logger.warning("warning")
    logger.warning({"some": "dict"})
    logger.info("info")
    logger.verbose("verbose")  # type: ignore
    logger.debug("debug")
