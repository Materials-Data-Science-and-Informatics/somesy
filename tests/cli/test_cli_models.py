from somesy.cli.models import SyncCommandOptions


def test_sync_command_options():
    options = SyncCommandOptions(
        input_file="test.toml",
        no_sync_cff=False,
        cff_file="CITATION.cff",
        no_sync_pyproject=False,
        pyproject_file="pyproject.toml",
        debug=True,
    )

    # test asdict without remove_keys
    options_dict = options.asdict()
    expected = {
        "input_file": "test.toml",
        "no_sync_cff": False,
        "cff_file": "CITATION.cff",
        "no_sync_pyproject": False,
        "pyproject_file": "pyproject.toml",
        "debug": True,
    }
    assert options_dict == expected

    # test asdict with remove_keys
    options_dict = options.asdict(remove_keys=["debug"])
    expected = {
        "input_file": "test.toml",
        "no_sync_cff": False,
        "cff_file": "CITATION.cff",
        "no_sync_pyproject": False,
        "pyproject_file": "pyproject.toml",
    }
    assert options_dict == expected
