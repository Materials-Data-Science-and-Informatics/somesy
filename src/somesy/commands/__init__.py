"""Commands for somesy."""

from .init_config import init_config, write_somesy_file
from .sync import sync

__all__ = ["init_config", "sync", "write_somesy_file"]
