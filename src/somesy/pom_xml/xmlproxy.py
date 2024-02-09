"""Wrapper to provide dict-like access to XML via ElementTree."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

import defusedxml.ElementTree as DET


class XMLProxy:
    """Class providing dict-like access to edit XML via ElementTree.

    Note that this wrapper facade is limited:
    * XML attributes are not supported
    * DTDs are ignored (arbitrary keys can be queried and added)
    * each tag is assumed to either contain a value or more nested tags
    * lists are treated atomically (no way to add/remove element from a collection)

    The semantics is implemented as follows:
    * If there are multiple tags with the same name, a list of XMLProxy nodes is returned
    * If a unique tag does have no nested tags, its `text` string value is returned
    * Otherwise the node is returned
    """

    # NOTE: one could create a separate XMLList wrapper to cover the list case better
    # but need to think through the semantics properly.

    def __init__(self, el: ET.Element, *, default_namespace: Optional[str] = None):
        """Wrap an existing XML ElementTree Element."""
        self._node: ET.Element = el
        self._def_ns = default_namespace

    def _qualified_key(self, key: str):
        """If passed key is not qualified, prepends the default namespace (if set)."""
        if key[0] == "{" or not self._def_ns:
            return key
        return "{" + self._def_ns + "}" + key

    @classmethod
    def parse(cls, path: Union[str, Path], **kwargs) -> XMLProxy:
        """Parse an XML file into an ElementTree, preserving comments."""
        path = path if isinstance(path, Path) else Path(path)
        parser = DET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        return cls(DET.parse(path, parser=parser).getroot(), **kwargs)

    def write(self, path: Union[str, Path], *, header: bool = True, **kwargs):
        """Write the XML DOM to an UTF-8 encoded file."""
        path = path if isinstance(path, Path) else Path(path)
        et = ET.ElementTree(self._node)
        if self._def_ns and "default_namespace" not in kwargs:
            kwargs["default_namespace"] = self._def_ns
        et.write(path, encoding="UTF-8", xml_declaration=header, **kwargs)

    def __repr__(self):
        """See `object.__repr__`."""
        return str(self._node)

    def __len__(self):
        """See `Mapping.__len__`."""
        return len(self._node)

    def __iter__(self):
        """See `Mapping.__iter__`."""
        return map(XMLProxy, iter(self._node))

    # ---- dict-like access ----

    def get(self, key: str, *, as_node_list: bool = False):
        """See `dict.get`."""
        if not key:
            raise ValueError("Key must not be an empty string!")
        # if not fully qualified + default NS is given, use it for query
        if lst := self._node.findall(self._qualified_key(key)):
            ns = list(map(lambda x: XMLProxy(x, default_namespace=self._def_ns), lst))
            if as_node_list:
                return ns  # return it as a list an any case if desired
            if len(ns) > 1:
                return ns  # node list (multiple matching elements)
            else:
                if ns[0]:  # single node (single matched element)
                    return ns[0]
                else:  # string value (leaf element, i.e. no inner tags)
                    return ns[0]._node.text.strip()

    def __getitem__(self, key: str):
        """Acts like `dict.__getitem__`, implemented with `get`."""
        val = self.get(key)
        if val is not None:
            return val
        else:
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Acts like `dict.__contains__`, implemented with `get`."""
        return self.get(key) is not None

    def __delitem__(self, key: str):
        """Acts like `dict.__delitem__`.

        If there are multiple matching tags, **all** of them are removed!
        """
        nodes = self.get(key, as_node_list=True)
        if not nodes:
            raise KeyError(key)
        for child in nodes:
            self._node.remove(child._node)

    def __setitem__(self, key: str, val):
        """See `dict.__setitem__`."""
        nodes = self.get(key, as_node_list=True)
        if nodes:
            if len(nodes) > 1:
                # delete all (we can't handle lists well) + create new
                del self[key]
                node = ET.SubElement(self._node, self._qualified_key(key))
            else:
                # take unique node and empty it out (text + inner tags)
                node = nodes[0]._node
                node.text = ""
                for child in iter(node):
                    node.remove(child)

        # attach value to the tag
        if not isinstance(val, (XMLProxy, list, dict)):  # leaf value
            val = val if isinstance(val, str) else str(val)
            node.text = val
        else:  # nested dict-like structure
            raise NotImplementedError
