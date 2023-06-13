import logging
from pathlib import Path

import pytest

from somesy.core import discover

logger = logging.getLogger("somesy")


def test_discover_input(mocker):
    # Test 1: input is is given and exists
    input = Path("tests/core/data/.somesy.toml")
    result = discover.discover_input(input)
    assert result == input

    # Test 2: input is is given but does not exist
    input = Path("tests/core/data/.somesy2.toml")
    result = discover.discover_input(input)
    assert result == Path(".somesy.toml")

    mocker.patch.object(discover, "INPUT_FILES_ORDERED", [])
    input = Path("tests/core/data/.somesy2.toml")
    with pytest.raises(FileNotFoundError):
        discover.discover_input(input)
