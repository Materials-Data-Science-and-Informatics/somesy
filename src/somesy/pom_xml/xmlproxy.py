"""Wrapper to provide dict-like access to XML via ElementTree."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import defusedxml.ElementTree as DET

# shallow type hint mostly for documentation purpose
JSONLike = Any


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

    def __init__(self, el: ET.Element, *, default_namespace: Optional[str] = None):
        """Wrap an existing XML ElementTree Element."""
        self._node: ET.Element = el
        self._def_ns = default_namespace

    def _wrap(self, el: ET.Element) -> XMLProxy:
        """Wrap different element, inheriting the namespace."""
        return XMLProxy(el, default_namespace=self._def_ns)

    def _qualified_key(self, key: str):
        """If passed key is not qualified, prepends the default namespace (if set)."""
        if key[0] == "{" or not self._def_ns:
            return key
        return "{" + self._def_ns + "}" + key

    def _shortened_key(self, key: str):
        """Inverse of `_qualified_key`."""
        if key[0] != "{" or not self._def_ns or key.find(self._def_ns) < 0:
            return key
        return key[key.find("}") + 1 :]

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
        """Return number of inner tags inside current XML element.

        Note that bool(node) thus checks whether an XML node is a leaf in the element tree.
        """
        return len(self._node)

    def __iter__(self):
        """Iterate the nested elements in-order."""
        return map(self._wrap, iter(self._node))

    def _dump(self):
        """Dump XML to stdout (for debugging)."""
        ET.dump(self._node)

    # ---- helpers ----

    def to_jsonlike(
        self, *, strip_default_ns: bool = True, keep_root: bool = False
    ) -> JSONLike:
        """Convert XML node to a JSON-like primitive, array or dict (ignoring attributes).

        Note that comments are ignored and all leaf values are strings.

        Args:
            strip_default_ns: Do not qualify keys from the default namespace
            keep_root: If true, the root tag name will be preserved (`{"root_tag": {...}}`)
        """
        if not len(self):  # leaf -> assume it's a primitive value
            return self._node.text.strip()

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
    def from_jsonlike_primitive(
        cls, val, *, elem_name: Optional[str] = None, **kwargs
    ) -> Union[str, XMLProxy]:
        """Convert a leaf node into a string value (i.e. return inner text).

        Returns a string (or an XML element, if elem_name is passed).
        """
        if val is None:
            ret = "null"  # turn None into Java null
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
    def from_jsonlike(cls, val, *, root_name: Optional[str] = None, **kwargs):
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
            return cls.from_jsonlike_primitive(val, elem_name=root_name, **kwargs)

        # now the dict case remains
        elem = ET.Element(root_name or "root")
        for k, v in val.items():
            if k.startswith(
                "__comment_"
            ):  # special key names are mapped to XML comments
                elem.append(ET.Comment(v if isinstance(v, str) else str(v)))

            elif isinstance(v, list):
                for vv in XMLProxy.from_jsonlike(v, root_name=k, **kwargs):
                    elem.append(vv)
            elif not isinstance(v, dict):  # primitive val
                # FIXME: use better case-splitting for type of function to avoid cast
                tmp = cast(
                    XMLProxy, XMLProxy.from_jsonlike_primitive(v, elem_name=k, **kwargs)
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
        if as_nodes and deep:
            raise ValueError("as_nodes and deep are mutually exclusive!")
        if not key:
            raise ValueError("Key must not be an empty string!")

        # if not fully qualified + default NS is given, use it for query
        if lst := self._node.findall(self._qualified_key(key)):
            ns: List[XMLProxy] = list(map(self._wrap, lst))
            if as_nodes:  # return it as a list of xml nodes
                return ns

            # apply canonical dict-ification
            ret: Union[List[XMLProxy], List[JSONLike]] = (
                ns if not deep else [x.to_jsonlike() for x in ns]
            )
            if ret:  # if list has just one element -> return that
                return lst[0] if len(lst) == 1 else lst

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

        self._node.text = ""
        for child in nodes:
            self._node.remove(child._node)

    def __setitem__(self, key: Union[str, XMLProxy], val: Union[JSONLike, XMLProxy]):
        """Add or overwrite an inner XML tag.

        If there is exactly one matching tag, the value is substituted in-place.
        If the passed value is a list, all list entries are added in their own element.

        If there are multiple existing matches, **all** existing elements are removed
        and the new value is added with as a new element (i.e. coming last)!

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
        # TODO: what about assigning a list of stuff? add that, then write tests

        if isinstance(key, str):
            nodes = self.get(key, as_nodes=True) or []
            if (
                len(nodes) > 1
            ):  # delete all existing elements in case there are multiple
                del self[key]
                nodes = []
            if not nodes:  # create new element if there were multiple or none
                node = self._wrap(ET.SubElement(self._node, self._qualified_key(key)))
            else:  # take the unique matching node, empty it out (text + inner tags)
                node = nodes[0]
        else:  # an XMLProxy object was passed as key -> use that
            node = key

        # ensure the target node is cleared out (e.g. when reusing existing element)
        node._node.text = ""
        for child in list(
            iter(node._node)
        ):  # need to store in list, removal invalidates iterator
            node._node.remove(child)

        # ensure value is represented as an XML node
        if not isinstance(val, XMLProxy):
            val = self.from_jsonlike(val, root_name=self._shortened_key(self._node.tag))
        else:
            wrapped = self._wrap(ET.Element("dummy"))
            wrapped._node.append(val._node)
            val = wrapped

        # transplant node contents into existing element (so it is inserted in-place)
        node._node.text = val._node.text
        for child in iter(val):
            node._node.append(child._node)
