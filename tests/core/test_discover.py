import logging
from pathlib import Path

import pytest

from somesy.core import discover
from somesy.core.utils import set_logger

logger = logging.getLogger("somesy")


@pytest.fixture(autouse=True)
def set_log():
    set_logger()


def test_discover_input(mocker):
    # Test 1: input is is given and exists
    input = "tests/core/data/.somesy.toml"
    result = discover.discover_input(input)
    assert result == Path(input)

    # Test 2: input is is given but does not exist
    input = "tests/core/data/.somesy2.toml"
    result = discover.discover_input(input)
    assert result == Path("pyproject.toml")

    mocker.patch.object(discover, "INPUT_FILES_ORDERED", [])
    input = "tests/core/data/.somesy2.toml"
    with pytest.raises(FileNotFoundError):
        discover.discover_input(input)