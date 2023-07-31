"""Integration with codemetapy (to re-generate codemeta as part of somesy sync)."""
import contextlib
import logging
from pathlib import Path

from ..core.models import SomesyConfig
from .exec import gen_codemeta
from .utils import cff_codemeta_tempfile, update_codemeta_file

log = logging.getLogger("somesy")


def collect_cm_sources(conf: SomesyConfig):
    """Assemble list of inputs for codemetapy based on somesy config.

    Returns files that are supported by both somesy and codemetapy and are enabled for somesy.
    """
    cm_sources = []
    if (
        not conf.no_sync_pyproject
        and conf.pyproject_file is not None
        and conf.pyproject_file.is_file()
    ):
        cm_sources.append(conf.pyproject_file)
    # NOTE: we don't add CFF directly, because it must be handled separately
    # NOTE: add other suitable somesy targets / codemeta sources (except CFF and codemeta) here
    if (
        not conf.no_sync_package_json
        and conf.package_json_file is not None
        and conf.package_json_file.is_file()
    ):
        cm_sources.append(conf.package_json_file)
    return cm_sources


def update_codemeta(conf: SomesyConfig) -> bool:
    """Generate or update codemeta file based on sources that somesy supports.

    Returns True if file has been written, False if it was up to date.
    """
    cm_sources = collect_cm_sources(conf)

    # if cff file is given, convert it to codemeta tempfile and pass as extra input
    temp_cff_cm = contextlib.nullcontext(None)
    if not conf.no_sync_cff and conf.cff_file is not None:
        temp_cff_cm = cff_codemeta_tempfile(conf.cff_file)
        cm_sources.append(Path(temp_cff_cm.name))

    # run codemetapy
    with temp_cff_cm:
        cm_harvest = gen_codemeta(cm_sources)

    # check output and write file if needed
    return update_codemeta_file(conf.codemeta_file, cm_harvest)


__all__ = ["update_codemeta"]
