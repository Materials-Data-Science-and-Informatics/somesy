"""somesy package."""

import importlib_metadata
from typing_extensions import Final

# Set version, it will use version from pyproject.toml if defined
__version__: Final[str] = importlib_metadata.version(__package__ or __name__)
