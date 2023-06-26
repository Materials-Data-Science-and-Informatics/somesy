"""Wrappers around codemetapy and cffconvert Python APIs."""
import json
import logging
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from typing import Dict, List

from cffconvert.cli.create_citation import create_citation
from codemeta.codemeta import build
from codemeta.serializers.jsonld import serialize_to_jsonld

log = logging.getLogger("somesy")


def cff_to_codemeta(cff_file: Path) -> Dict:
    """Get codemeta LD dict from CITATION.cff via cffconvert."""
    return json.loads(create_citation(cff_file, None).as_codemeta())


def gen_codemeta(sources: List[str], *, with_entrypoints: bool = True) -> Dict:
    """Harvest codemeta LD dict via codemetapy."""
    log.debug(f"Running codemetapy with sources {sources}")
    with redirect_stderr(StringIO()) as cm_log:
        g, res, args, _ = build(
            inputsources=list(map(str, sources)),
            output="json",
            with_entrypoints=with_entrypoints,
        )
    # add captured codemetapy log into our log
    log.debug(f"codemetapy log:\n----\n{cm_log.getvalue()}\n----")

    return serialize_to_jsonld(g, res, args)
