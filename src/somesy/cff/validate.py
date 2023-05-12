"""Validate a citation.cff file."""
from pathlib import Path

from cffconvert.cli.create_citation import create_citation


def validate_citation(cff_path: Path) -> bool:
    """Validate a citation.cff file."""
    try:
        # load the citation metadata from the specified source and create a Python object representation of it
        citation = create_citation(cff_path, None)
        citation.validate()
        return True
    except Exception:
        return False
