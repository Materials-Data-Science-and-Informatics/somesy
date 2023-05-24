"""Validate a citation.cff file."""
import logging
from pathlib import Path

from cffconvert.cli.create_citation import create_citation

logger = logging.getLogger("somesy")


def validate_citation(cff_path: Path) -> None:
    """Validate a citation.cff file."""
    try:
        # load the citation metadata from the specified source and create a Python object representation of it
        citation = create_citation(cff_path, None)
        citation.validate()
    except ValueError as e:
        raise ValueError(f"CITATION.cff file is not valid!\n{e}") from e
