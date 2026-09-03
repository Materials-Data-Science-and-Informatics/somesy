import logging

import pytest
from typer.testing import CliRunner

from somesy.core.log import SomesyLogLevel, set_log_level
from somesy.main import app

runner = CliRunner()
logger = logging.getLogger("somesy")


def test_app_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "somesy version: " in result.stdout


def test_sync_options_have_unique_shortcuts():
    result = runner.invoke(app, ["sync", "--help"])

    assert result.exit_code == 0
    assert "-P" in result.stdout and "--no-sync-pyproject" in result.stdout
    assert "-V" in result.stdout and "--pass-validation" in result.stdout
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
