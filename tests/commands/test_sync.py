from pathlib import Path

from somesy.commands.sync import sync
from somesy.core.models import SomesyConfig


def test_sync(tmp_path, create_poetry_file):
    input_file = Path("tests/commands/data/.somesy.toml")
    cff_file = tmp_path / "CITATION.cff"
    pyproject_file = tmp_path / "pyproject.toml"

    # create pyproject file beforehand
    create_poetry_file(pyproject_file)

    # TEST 1: sync only pyproject.toml
    conf = SomesyConfig(
        input_file=input_file, pyproject_file=pyproject_file, no_sync_cff=True
    )
    sync(conf)
    assert pyproject_file.is_file()
    assert cff_file.is_file() is False

    # delete pyproject.toml
    pyproject_file.unlink()

    # TEST 2: sync only CITATION.cff
    conf = SomesyConfig(
        input_file=input_file, no_sync_pyproject=True, cff_file=cff_file
    )
    sync(conf)
    assert pyproject_file.is_file() is False
    assert cff_file.is_file()

    # delete files
    cff_file.unlink()

    # create pyproject file beforehand
    create_poetry_file(pyproject_file)

    # TEST 3: sync both pyproject.toml and CITATION.cff
    conf = SomesyConfig(
        input_file=input_file, pyproject_file=pyproject_file, cff_file=cff_file
    )
    sync(conf)
    assert pyproject_file.is_file()
    assert cff_file.is_file()
