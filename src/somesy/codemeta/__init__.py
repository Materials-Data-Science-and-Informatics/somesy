"""Integration with codemetapy (to re-generate codemeta as part of somesy sync)."""
import logging
from pathlib import Path
from typing import Optional

from .exec import gen_codemeta
from .utils import cff_codemeta_tempfile, update_codemeta_file

log = logging.getLogger("somesy")


def update_codemeta(cm_file: Path, cff_file: Optional[Path]) -> bool:
    """Generate or update codemeta file based on sources that somesy supports.

    Returns True if file has been written, False if it was up to date.
    """
    log.verbose("Updating codemeta.json file.")

    # NOTE: other files that should be listed here are files
    # * supported by somesy, and
    # * enabled by somesy config (created/synced), and
    # * supported by codemetapy
    cm_sources = ["pyproject.toml"]

    # if cff file is given, convert it to codemeta and pass as extra input
    temp_cff_cm = None
    if cff_file is not None:
        temp_cff_cm = cff_codemeta_tempfile(cff_file)
        cm_sources.append(temp_cff_cm.name)

    # harvest suitable files
    cm_harvest = gen_codemeta(cm_sources)

    if temp_cff_cm is not None:
        # close + auto-remove temp file
        temp_cff_cm.close()

    if update_codemeta_file(cm_file, cm_harvest):
        log.verbose(f"New codemeta graph written to {cm_file}.")
        return True
    else:
        log.verbose(f"Codemeta graph unchanged, keeping old {cm_file}.")
        return False


__all__ = ["update_codemeta"]
