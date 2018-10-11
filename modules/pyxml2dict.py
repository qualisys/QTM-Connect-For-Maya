#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Auth : mjrao
# @Time : 2017/8/4 16:50


import xml.etree.ElementTree as ET
from collections import defaultdict

__all__ = ['XML2Dict']


class XML2Dict(object):
    def __init__(self, coding='UTF-8'):
        self._coding = coding
        self.remove_ns = False

    def _parse_node(self, t):
        ttag = t.tag
        if self.remove_ns:
            ttag = self._remove_namespace(ttag)
        d = {ttag: {} if t.attrib else None}  # the variable 'd' is the constructed target dictionary
        # 't.tag' if have values, it is the first layer of the dictionary
        children = list(t)  # The following recursive traverse processing tree, until the leaf node
        if children:  # Determine whether the node is empty, recursive boundary conditions
            dd = defaultdict(list)
            for dc in map(self._parse_node, children):  # recursive traverse processing tree
                for k, v in dc.iteritems():
                    dd[k].append(v)
            d = {ttag: {k: v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}  # handle child node
        if t.attrib:  # handle attributes,prefix all of the stored attributes @
            d[ttag].update(('@' + k, v) for k, v in t.attrib.iteritems())
        if t.text:
            text = t.text.strip().encode(self._coding)  # strip blank space
            if children or t.attrib:
                d[ttag]['#text'] = text
            else:
                d[ttag] = text  # the text value as t.tag
        return d

    def parse(self, xml_file):
        with open(xml_file, 'r') as fp:
            return self.fromstring(fp.read())

    def fromstring(self, xml_str, remove_namespace=False):
        self.remove_ns = remove_namespace
        t = ET.fromstring(xml_str)
        return self._parse_node(t)

    def _remove_namespace(self, tag):
        if tag.find("{") >= 0 and tag.find("}") >= 0:
            return tag[:tag.find("{")] + tag[(tag.find("}")+1):]
        else:
            return tag
