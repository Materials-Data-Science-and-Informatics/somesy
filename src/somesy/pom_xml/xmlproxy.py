"""Wrapper to provide dict-like access to XML via ElementTree."""

from typing import Mapping


class XMLProxy(Mapping):
    """Class providing dict-like access to edit XML via ElementTree."""
