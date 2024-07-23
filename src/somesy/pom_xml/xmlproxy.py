"""Wrapper to provide dict-like access to XML via ElementTree."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import defusedxml.ElementTree as DET

# shallow type hint mostly for documentation purpose
JSONLike = Any


def load_xml(path: Path) -> ET.ElementTree:
    """Parse an XML file into an ElementTree, preserving comments."""
    path = path if isinstance(path, Path) else Path(path)
    parser = DET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return DET.parse(path, parser=parser)


def indent(elem, level=0):
    """Indent the elements of this XML node (i.e. pretty print)."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for el in elem:
            indent(el, level + 1)
        if not el.tail or not el.tail.strip():
            el.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class XMLProxy:
    """Class providing dict-like access to edit XML via ElementTree.

    Note that this wrapper facade is limited to a restricted (but useful) subset of XML:
    * XML attributes are not supported
    * DTDs are ignored (arbitrary keys can be queried and added)
    * each tag is assumed to EITHER contain text OR more nested tags
    * lists are treated atomically (no way to add/remove element from a collection)

    The semantics is implemented as follows:

    * If there are multiple tags with the same name, a list of XMLProxy nodes is returned
    * If a unique tag does have no nested tags, its `text` string value is returned
    * Otherwise, the node is returned
    """

    def _wrap(self, el: ET.Element) -> XMLProxy:
        """Wrap a different element, inheriting the same namespace."""
        return XMLProxy(el, default_namespace=self._def_ns)

    def _dump(self):
        """Dump XML to stdout (for debugging)."""
        ET.dump(self._node)

    def _qualified_key(self, key: str):
        """If passed key is not qualified, prepends the default namespace (if set)."""
        if key[0] == "{" or not self._def_ns:
            return key
        return "{" + self._def_ns + "}" + key

    def _shortened_key(self, key: str):
        """Inverse of `_qualified_key` (strips default namespace from element name)."""
        if key[0] != "{" or not self._def_ns or key.find(self._def_ns) < 0:
            return key
        return key[key.find("}") + 1 :]

    # ----

    def __init__(self, el: ET.Element, *, default_namespace: Optional[str] = None):
        """Wrap an existing XML ElementTree Element."""
        self._node: ET.Element = el
        self._def_ns = default_namespace

    @classmethod
    def parse(cls, path: Union[str, Path], **kwargs) -> XMLProxy:
        """Parse an XML file into a wrapped ElementTree, preserving comments."""
        path = path if isinstance(path, Path) else Path(path)
        return cls(load_xml(path).getroot(), **kwargs)

    def write(self, path: Union[str, Path], *, header: bool = True, **kwargs):
        """Write the XML DOM to an UTF-8 encoded file."""
        path = path if isinstance(path, Path) else Path(path)
        et = ET.ElementTree(self._node)
        if self._def_ns and "default_namespace" not in kwargs:
            kwargs["default_namespace"] = self._def_ns
        indent(et.getroot())
        et.write(path, encoding="UTF-8", xml_declaration=header, **kwargs)

    def __repr__(self):
        """See `object.__repr__`."""
        return str(self._node)

    def __len__(self):
        """Return number of inner tags inside current XML element.

        Note that bool(node) thus checks whether an XML node is a leaf in the element tree.
        """
        return len(self._node)

    def __iter__(self):
        """Iterate the nested elements in-order."""
        return map(self._wrap, iter(self._node))

    @property
    def namespace(self) -> Optional[str]:
        """Default namespace of this node."""
        return self._def_ns

    @property
    def is_comment(self):
        """Return whether the current element node is an XML comment."""
        return not isinstance(self._node.tag, str)

    @property
    def tag(self) -> Optional[str]:
        """Return tag name of this element (unless it is a comment)."""
        if self.is_comment:
            return None
        return self._shortened_key(self._node.tag)

    @tag.setter
    def tag(self, val: str):
        """Set the tag of this element."""
        if self.is_comment:
            raise ValueError("Cannot set tag name for comment element!")
        self._node.tag = self._qualified_key(val)

    # ---- helpers ----

    def to_jsonlike(
        self,
        *,
        strip_default_ns: bool = True,
        keep_root: bool = False,
    ) -> JSONLike:
        """Convert XML node to a JSON-like primitive, array or dict (ignoring attributes).

        Note that all leaf values are strings (i.e. not parsed to bool/int/float etc.).

        Args:
            strip_default_ns: Do not qualify keys from the default namespace
            keep_root: If true, the root tag name will be preserved (`{"root_tag": {...}}`)

        """
        if not len(self):  # leaf -> assume it's a primitive value
            return self._node.text or ""

        dct = {}
        ccnt = 0
        for elem in iter(self):
            raw = elem._node
            if not isinstance(raw.tag, str):
                ccnt += 1
                key = f"__comment_{ccnt}__"
            else:
                key = raw.tag if not strip_default_ns else self._shortened_key(raw.tag)

            curr_val = elem.to_jsonlike(strip_default_ns=strip_default_ns)
            if key not in dct:
                dct[key] = curr_val
                continue
            val = dct[key]
            if not isinstance(val, list):
                dct[key] = [dct[key]]
            dct[key].append(curr_val)

        return dct if not keep_root else {self._shortened_key(self._node.tag): dct}

    @classmethod
    def _from_jsonlike_primitive(
        cls, val, *, elem_name: Optional[str] = None, **kwargs
    ) -> Union[str, XMLProxy]:
        """Convert a leaf node into a string value (i.e. return inner text).

        Returns a string (or an XML element, if elem_name is passed).
        """
        if val is None:
            ret = ""  # turn None into empty string
        elif isinstance(val, str):
            ret = val
        elif isinstance(val, bool):
            ret = str(val).lower()  # True -> true / False -> false
        elif isinstance(val, (int, float)):
            ret = str(val)
        else:
            raise TypeError(
                f"Value of type {type(val)} is not JSON-like primitive: {val}"
            )

        if not elem_name:
            return ret
        else:  # return the value wrapped as an element (needed in from_jsonlike)
            elem = ET.Element(elem_name)
            elem.text = ret
            return cls(elem, **kwargs)

    @classmethod
    def from_jsonlike(
        cls, val: JSONLike, *, root_name: Optional[str] = None, **kwargs: Any
    ):
        """Convert a JSON-like primitive, array or dict into an XML element.

        Note that booleans are serialized as `true`/`false` and None as `null`.

        Args:
            val: Value to convert into an XML element.
            root_name: If `val` is a dict, defines the tag name for the root element.
            kwargs: Additional arguments for XML element instantiation.

        """
        if isinstance(val, list):
            return list(
                map(lambda x: cls.from_jsonlike(x, root_name=root_name, **kwargs), val)
            )
        if not isinstance(val, dict):  # primitive val
            return cls._from_jsonlike_primitive(val, elem_name=root_name, **kwargs)

        # now the dict case remains
        elem = ET.Element(root_name or "root")
        for k, v in val.items():
            if k.startswith(
                "__comment_"
            ):  # special key names are mapped to XML comments
                elem.append(ET.Comment(v if isinstance(v, str) else str(v)))

            elif isinstance(v, list):
                for vv in XMLProxy.from_jsonlike(v, root_name=k, **kwargs):
                    elem.append(vv._node)
            elif not isinstance(v, dict):  # primitive val
                # FIXME: use better case-splitting for type of function to avoid cast
                tmp = cast(
                    XMLProxy,
                    XMLProxy._from_jsonlike_primitive(v, elem_name=k, **kwargs),
                )
                elem.append(tmp._node)
            else:  # dict
                elem.append(XMLProxy.from_jsonlike(v, root_name=k)._node)

        return cls(elem, **kwargs)

    # ---- dict-like access ----

    def get(self, key: str, *, as_nodes: bool = False, deep: bool = False):
        """Get sub-structure(s) of value(s) matching desired XML tag name.

        * If there are multiple matching elements, will return them all as a list.
        * If there is a single matching element, will return that element without a list.

        Args:
            key: tag name to retrieve
            as_nodes: If true, will *always* return a list of (zero or more) XML nodes
            deep: Expand nested XML elements instead of returning them as XML nodes

        """
        # NOTE: could allow to retrieve comments when using empty string/none as key?

        if as_nodes and deep:
            raise ValueError("as_nodes and deep are mutually exclusive!")
        if not key:
            raise ValueError("Key must not be an empty string!")
        key = self._qualified_key(key)

        # if not fully qualified + default NS is given, use it for query
        lst = self._node.findall(key)
        ns: List[XMLProxy] = list(map(self._wrap, lst))
        if as_nodes:  # return it as a list of xml nodes
            return ns
        if not ns:  # no element
            return None

        ret = ns if not deep else [x.to_jsonlike() for x in ns]
        if len(ret) == 1:
            return ret[0]  # single element
        else:
            return ret

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

    def __delitem__(self, key: Union[str, XMLProxy]):
        """Delete a nested XML element with matching key name.

        Note that **all** XML elements with the given tag name are removed!

        To prevent this behavior, instead of a string tag name you can provide the
        exact element to be removed, i.e. if a node `node_a` represents the following XML:

        ```
        <a>
          <b>1</b>
          <c>2</c>
          <b>3</b>
        </a>
        ```

        Then we have that:

        * `del node_a["b"]` removes **both** tags, leaving just the `c` tag.
        * `del node_a[node_a["a"][1]]` removes just the second tag with the `3`.
        """
        if isinstance(key, str):
            nodes = self.get(key, as_nodes=True)
        else:
            nodes = [key] if key._node in self._node else []

        if not nodes:
            raise KeyError(key)

        if self._node.text is not None:
            self._node.text = ""
        for child in nodes:
            self._node.remove(child._node)

    def _clear(self):
        """Remove contents of this XML element (e.g. for overwriting in-place)."""
        self._node.text = ""
        children = list(iter(self._node))  # need to store, removal invalidates iterator
        for child in children:
            self._node.remove(child)

    def __setitem__(self, key: Union[str, XMLProxy], val: Union[JSONLike, XMLProxy]):
        """Add or overwrite an inner XML tag.

        If there is exactly one matching tag, the value is substituted in-place.
        If the passed value is a list, all list entries are added in their own element.

        If there are multiple existing matches or target values, then
        **all** existing elements are removed and the new value(s) are added in
        new element(s) (i.e. coming after other unrelated existing elements)!

        To prevent this behavior, instead of a string tag name you can provide the
        exact element to be overwritten, i.e. if a node `node_a` represents the following XML:

        ```
        <a>
          <b>1</b>
          <c>2</c>
          <b>3</b>
        </a>
        ```

        Then we have that:

        * `node_a["b"] = 5` removes both existing tags and creates a new tag with the passed value(s).
        * `node_a[node_a["b"][1]] = 5` replaces the `3` in the second tag with the `5`.

        Note that the passed value must be either an XML element already, or be a pure JSON-like object.
        """
        if isinstance(key, str):
            nodes = self.get(key, as_nodes=True)
            # delete all existing elements if multiple exist or are passed
            if len(nodes) > 1 or (len(nodes) and isinstance(val, list)):
                del self[key]
                nodes = []
            # now we can assume there's zero or one suitable target elements
            if nodes:  # if it is one, clear it out
                nodes[0]._clear()
        else:  # an XMLProxy object was passed as key -> try to use that
            if isinstance(val, list):
                raise ValueError(
                    "Cannot overwrite a single element with a list of values!"
                )
            # ensure the target node is cleared out and use it as target
            key._clear()
            nodes = [key]
            key = key.tag

        # ensure key string is qualified with a namespace
        key_name: str = self._qualified_key(key)

        # normalize passed value(s) to be list (general case)
        vals = val if isinstance(val, list) else [val]

        # ensure there is the required number of target element nodes
        for _ in range(len(vals) - len(nodes)):
            nodes.append(self._wrap(ET.SubElement(self._node, key_name)))

        # normalize values no XML element nodes
        nvals = []
        for val in vals:
            # ensure value is represented as an XML node
            if isinstance(val, XMLProxy):
                obj = self._wrap(ET.Element("dummy"))
                obj._node.append(val._node)
            else:
                obj = self.from_jsonlike(val, root_name=key_name)

            nvals.append(obj)

        for node, val in zip(nodes, nvals):
            # transplant node contents into existing element (so it is inserted in-place)
            node._node.text = val._node.text
            for child in iter(val):
                node._node.append(child._node)
