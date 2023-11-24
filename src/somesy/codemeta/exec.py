"""Wrappers around codemetapy and cffconvert Python APIs."""
import json
import logging
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from typing import Dict, List

from cffconvert.cli.create_citation import create_citation

log = logging.getLogger("somesy")

# ----
# TODO: remove this section once windows path issue is fixed
_patched = False


def patch_codemetapy():
    """Monkey-patch for codemetapy (< 2.5.2)."""
    global _patched
    from importlib_metadata import version

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
            log.info("called patched init")
            unfix_local_sources()
            # NOTE: do not fix sources here, init_graph chokes on it
            # ret = [(fix(a), b) for a, b in init_context(*args, **kwargs)]
            ret = init_context(*args, **kwargs)
            fix_local_sources()
            return ret

        cmc.init_context = patched_init_context


if not _patched:
    patch_codemetapy()
# ----


def cff_to_codemeta(cff_file: Path) -> Dict:
    """Get codemeta LD dict from CITATION.cff via cffconvert."""
    return json.loads(create_citation(cff_file, None).as_codemeta())


def gen_codemeta(sources: List[str], *, with_entrypoints: bool = True) -> Dict:
    """Harvest codemeta LD dict via codemetapy."""
    log.debug(f"Running codemetapy with sources {sources}")

    from codemeta.codemeta import build  # noqa
    from codemeta.serializers.jsonld import serialize_to_jsonld  # noqa

    with redirect_stderr(StringIO()) as cm_log:
        g, res, args, _ = build(
            inputsources=list(map(str, sources)),
            output="json",
            with_entrypoints=with_entrypoints,
        )
    # add captured codemetapy log into our log
    log.debug(f"codemetapy log:\n----\n{cm_log.getvalue()}\n----")

    return serialize_to_jsonld(g, res, args)
