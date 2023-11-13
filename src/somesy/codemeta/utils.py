"""Helpers to work around issue with non-deterministic serialization."""

import importlib.resources
import json
import logging
import platform
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

import rdflib
import rdflib.compare

from somesy import __tmp_dir__

from .exec import cff_to_codemeta

log = logging.getLogger("somesy")

# assembled context (manually downloaded and combined in a JSON array)
_CM_CONTEXT_FILE = "codemeta_context_2023-04-19.json"

# load codemeta context
with importlib.resources.open_text(__package__, _CM_CONTEXT_FILE) as c:
    _CM_CONTEXT = json.load(c)

# expected URLs
_codemeta_context = set(
    [
        "https://doi.org/10.5063/schema/codemeta-2.0",
        "https://w3id.org/software-iodata",
        "https://raw.githubusercontent.com/jantman/repostatus.org/"
        "master/badges/latest/ontology.jsonld",
        "https://schema.org",
        "https://w3id.org/software-types",
    ]
)


def _localize_codemetapy_context(json):
    """Prevent rdflib external context resolution by embedding it from a file.

    The context is required to parse the JSON-LD correctly, fields with no
    context are ignored (not considered LD).
    """
    context = json.get("@context") or []

    # remove dicts from context
    # (they are not supported by rdflib, and we don't need them anyway)
    context = [c for c in context if not isinstance(c, dict)]
    ctx = set(context)
    if not ctx:
        # probably empty or not codemeta, nothing to do
        return json

    if ctx != _codemeta_context:
        msg = f"Unexpected codemeta context: {json['@context']}. Is this really from codemetapy?"
        raise RuntimeError(msg)

    ret = dict(json)
    ret.update({"@context": _CM_CONTEXT})

    return ret


def serialize_codemeta(cm: Dict) -> str:
    """Convert JSON Dict to str (using settings like codemetapy)."""
    # using settings like in codemetapy
    return json.dumps(cm, indent=4, ensure_ascii=False, sort_keys=True)


def _graph_from_cm_dict(graph_dict):
    """Returns codemeta with localized context from a dict produced by codemetapy."""
    g = rdflib.Graph()
    expanded = json.dumps(_localize_codemetapy_context(graph_dict))
    g.parse(data=expanded, format="json-ld")
    return g


def _graph_from_cm_file(file: Path) -> rdflib.Graph:
    """Returns loaded codemeta with localized context.

    If file does not exist, returns `None` (to distinguish from existing but empty).
    """
    if file.is_file():
        with open(file, "r") as f:
            graph_dict = json.load(f)
            return _graph_from_cm_dict(graph_dict)


# ----


def update_codemeta_file(cm_file: Path, cm_dict: Dict) -> bool:
    """Update codemeta file with graph in dict if it changed.

    Returns True if the file update happened.
    """
    old = _graph_from_cm_file(cm_file) or rdflib.Graph()
    new = _graph_from_cm_dict(cm_dict)

    if not rdflib.compare.isomorphic(old, new):
        with open(cm_file, "w") as f:
            f.write(serialize_codemeta(cm_dict))
        return True
    return False


def cff_codemeta_tempfile(cff_file: Path):
    """Returns named temporary file with codemeta export of citation file."""
    cm_cff = cff_to_codemeta(cff_file)
    temp_cff_cm = NamedTemporaryFile(prefix="cff_cm_", suffix=".json", delete=False)

    # if the OS is windows we need to set the TMPDIR environment variable
    if platform.system() == "Windows":
        temp_cff_cm = NamedTemporaryFile(
            prefix="cff_cm_", suffix=".json", delete=False, dir=__tmp_dir__
        )

    temp_cff_cm.write(json.dumps(cm_cff).encode("utf-8"))
    temp_cff_cm.flush()  # needed, or it won't be readable yet
    return temp_cff_cm
