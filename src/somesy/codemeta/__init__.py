"""Integration with codemetapy (to re-generate codemeta as part of somesy sync)."""
import logging

from importlib_metadata import version

from ..core.models import SomesyConfig
from .exec import gen_codemeta
from .utils import (
    cff_codemeta_tempfile,
    cleanup_codemeta_tempfiles,
    update_codemeta_file,
)

log = logging.getLogger("somesy")


_patched = False


def patch_codemetapy():
    """Monkey-patch for codemetapy (< 2.5.2)."""
    global _patched
    # TODO: remove once windows path issue is fixed
    if version("codemetapy") >= "2.5.2":
        return

    import codemeta.common as cmc

    def fix(path: str) -> str:
        """Ensure the windows file URI is valid (starts with file:///)."""
        if path.startswith("file://") and not path.startswith("file:///"):
            return path.replace("file://", "file:///")
        return path

    def unfix(path: str) -> str:
        if path.startswith("file:///") and path[9] == ":":  # windows partition name
            return path.replace("file:///", "file://")
        return path

    def fix_local_sources():
        cmc.SCHEMA_LOCAL_SOURCE = fix(cmc.SCHEMA_LOCAL_SOURCE)
        cmc.CODEMETA_LOCAL_SOURCE = fix(cmc.CODEMETA_LOCAL_SOURCE)
        cmc.STYPE_LOCAL_SOURCE = fix(cmc.STYPE_LOCAL_SOURCE)
        cmc.IODATA_LOCAL_SOURCE = fix(cmc.IODATA_LOCAL_SOURCE)
        cmc.REPOSTATUS_LOCAL_SOURCE = fix(cmc.REPOSTATUS_LOCAL_SOURCE)

    def unfix_local_sources():
        cmc.SCHEMA_LOCAL_SOURCE = unfix(cmc.SCHEMA_LOCAL_SOURCE)
        cmc.CODEMETA_LOCAL_SOURCE = unfix(cmc.CODEMETA_LOCAL_SOURCE)
        cmc.STYPE_LOCAL_SOURCE = unfix(cmc.STYPE_LOCAL_SOURCE)
        cmc.IODATA_LOCAL_SOURCE = unfix(cmc.IODATA_LOCAL_SOURCE)
        cmc.REPOSTATUS_LOCAL_SOURCE = unfix(cmc.REPOSTATUS_LOCAL_SOURCE)

    fix_local_sources()

    if not _patched:
        _patched = True

        init_context = cmc.init_context

        def patched_init_context(*args, **kwargs):
            unfix_local_sources()
            ret = [(fix(a), b) for a, b in init_context(*args, **kwargs)]
            fix_local_sources()
            return ret

        cmc.init_context = patched_init_context


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
        conf.no_sync_package_json
        and conf.package_json_file is not None
        and conf.package_json_file.is_file()
    ):
        cm_sources.append(conf.package_json_file)
    return cm_sources


def update_codemeta(conf: SomesyConfig):
    """Generate or update codemeta file based on sources that somesy supports.

    Returns True if file has been written, False if it was up to date.
    """
    cm_sources = collect_cm_sources(conf)

    # if cff file is given, convert it to codemeta tempfile and pass as extra input
    if not conf.no_sync_cff and conf.cff_file is not None:
        temp_cff_cm = cff_codemeta_tempfile(conf.cff_file)
        cm_sources.append(temp_cff_cm.resolve())

    # run codemetapy
    patch_codemetapy()
    cm_harvest = gen_codemeta(cm_sources)

    # NOTE: once codemetapy is fixed (still broken with 2.5.1), we should not need
    # update_codemeta_file + codemeta context dump + most of utils.py + their tests anymore
    # we'll first disable the workaround and see for a while if everything works
    # as expected, and if it does, the cleanup can be completed.
    #
    # save to file with same settings as used by codemetapy
    # with open(conf.codemeta_file, "w") as f:
    #     f.write(json.dumps(cm_harvest, indent=4, ensure_ascii=False, sort_keys=True))

    # check output and write file if needed (with workaround checking graph equivalence)
    result = update_codemeta_file(conf.codemeta_file, cm_harvest)

    # cleanup
    cleanup_codemeta_tempfiles()
    return result


__all__ = ["update_codemeta"]
