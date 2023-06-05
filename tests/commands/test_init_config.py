import pytest

from somesy.cli.models import SyncCommandOptions
from somesy.commands.init_config import init_config
from somesy.core.utils import set_logger


@pytest.fixture(autouse=True)
def set_log():
    set_logger()


def test_init_config(
    tmp_path, create_somesy_metadata, create_somesy_metadata_config, create_poetry_file
):
    # load empty file
    reject_file = tmp_path / ".somesy.reject.toml"
    reject_file.touch()
    with pytest.raises(ValueError):
        init_config(reject_file, SyncCommandOptions(debug=True))

    # load somesy file
    somesy_file = tmp_path / ".somesy.toml"
    create_somesy_metadata(somesy_file)
    init_config(somesy_file, SyncCommandOptions(debug=True))
    assert "debug = true" in somesy_file.read_text()

    # load somesy file with config
    somesy_file = tmp_path / ".somesy.with_config.toml"
    create_somesy_metadata_config(somesy_file)
    init_config(somesy_file, SyncCommandOptions(show_info=True))
    assert "show_info = true" in somesy_file.read_text()

    # load pyproject file
    pyproject_file = tmp_path / "pyproject.toml"
    create_poetry_file(pyproject_file)
    init_config(pyproject_file, SyncCommandOptions(debug=True))
    assert "debug = true" in pyproject_file.read_text()
