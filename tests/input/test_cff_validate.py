import pytest
from ruamel.yaml import YAML

from somesy.cff.writer import CFF


def test_cff_validate_accept(load_files, file_types):
    """Validate by loading the data cff file using the fixture."""
    load_files([file_types.CITATION])


def test_cff_validate_reject(tmp_path):
    """Test validating a CFF file."""
    cff_path = tmp_path / "CITATION.cff"

    # create a CFF file with a invalid version
    reject_cff_object = {
        "version": "1.4.0",
        "message": "If you use this software, please cite it using these metadata.",
        "type": "software",
    }
    yaml = YAML()
    yaml.dump(reject_cff_object, cff_path)

    # try to load the CFF file
    with pytest.raises(ValueError):
        CFF(cff_path)
