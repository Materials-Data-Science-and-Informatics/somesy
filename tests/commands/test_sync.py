from pathlib import Path

import pytest

from somesy.commands.sync import sync
from somesy.core.utils import set_logger


@pytest.fixture(autouse=True)
def set_log():
    set_logger()


def test_sync(tmp_path):
    input_file = Path("tests/commands/data/.somesy.toml")
    cff_file = tmp_path / "CITATION.cff"
    pyproject_file = tmp_path / "pyproject.toml"

    # TEST 1: no output file specified
    with pytest.raises(ValueError):
        sync(input_file=input_file)

    # TEST 2: sync only pyproject.toml
    sync(input_file=input_file, pyproject_file=pyproject_file)
    assert pyproject_file.exists()
    assert cff_file.exists() is False

    # delete pyproject.toml
    pyproject_file.unlink()

    # TEST 3: sync only CITATION.cff
    sync(input_file=input_file, cff_file=cff_file)
    assert pyproject_file.exists() is False
    assert cff_file.exists()

    # delete files
    cff_file.unlink()

    # TEST 4: sync both pyproject.toml and CITATION.cff
    sync(input_file=input_file, pyproject_file=pyproject_file, cff_file=cff_file)
    assert pyproject_file.exists()
    assert cff_file.exists()
