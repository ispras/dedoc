# Copyright 2020 IBM
# Author: peter.zhong@au1.ibm.com
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the Apache 2.0 License.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Apache 2.0 License for more details.

# Source: https://github.com/ibm-aur-nlp/PubTabNet

import distance
from apted import APTED, Config
from apted.helpers import Tree
from lxml import etree, html
from collections import deque

from tqdm import tqdm


class TableTree(Tree):
    def __init__(self, tag, colspan=None, rowspan=None, content=None, visible=None, *children):
        self.tag = tag
        self.colspan = colspan
        self.rowspan = rowspan
        self.content = content
        self.visible = visible
        self.children = list(children)

    def bracket(self):
        """Show tree using brackets notation
        """
        if self.tag == "td":
            result = f'"tag": {self.tag}, "colspan": {self.colspan}, "rowspan": {self.rowspan}, "text": {self.content}'
        else:
            result = f'"tag": {self.tag}'
        for child in self.children:
            result += child.bracket()
        return "{{" + result + "}}"


class CustomConfig(Config):
    @staticmethod
    def maximum(*sequences):
        """Get maximum possible value
        """
        return max(map(len, sequences))

    def normalized_distance(self, *sequences) -> float:
        """Get distance from 0 to 1
        """
        return float(distance.levenshtein(*sequences)) / self.maximum(*sequences)

    def rename(self, node1: TableTree, node2: TableTree) -> float:
        """Compares attributes of trees"""
        if (node1.tag != node2.tag) or (node1.colspan != node2.colspan) or (node1.rowspan != node2.rowspan):
            return 1.
        if node1.tag == "td":
            if not node1.visible or not node2.visible:
                return 0.
            if node1.content or node2.content:
                return self.normalized_distance(node1.content, node2.content)
        return 0.


class TEDS(object):
    """ Tree Edit Distance based Similarity
    """

    def __init__(self, structure_only=False, n_jobs=1, ignore_nodes=None):
        assert isinstance(n_jobs, int) and (n_jobs >= 1), "n_jobs must be an integer greather than 1"
        self.structure_only = structure_only
        self.n_jobs = n_jobs
        self.ignore_nodes = ignore_nodes
        self.__tokens__ = []

    def tokenize(self, node):
        """ Tokenizes table cells
        """
        self.__tokens__.append(f"<{node.tag}>")
        if node.text is not None:
            self.__tokens__ += list(node.text)
        for n in node.getchildren():
            self.tokenize(n)
        if node.tag != "unk":
            self.__tokens__.append(f"</{node.tag}>")
        if node.tag != "td" and node.tail is not None:
            self.__tokens__ += list(node.tail)

    def load_html_tree(self, node, parent=None):
        """ Converts HTML tree to the format required by apted
        """
        if node.tag == "td":
            if self.structure_only:
                cell = []
            else:
                self.__tokens__ = []
                self.tokenize(node)
                cell = self.__tokens__[1:-1].copy()

            try:
                new_node = TableTree(tag=node.tag,
                                     colspan=int(node.attrib.get("colspan", "1")),
                                     rowspan=int(node.attrib.get("rowspan", "1")),
                                     content=cell,
                                     visible=False if node.attrib.get("style") == "display: none" else True, *deque())
            except Exception as ex:
                print(f"Bad html file. HTML parse exception. Exception's msg: {ex}")
                raise ex
        else:
            new_node = TableTree(node.tag, None, None, None, True, *deque())
        if parent is not None:
            parent.children.append(new_node)
        if node.tag != "td":
            for n in node.getchildren():
                self.load_html_tree(n, new_node)
        if parent is None:
            return new_node

    def evaluate(self, pred: str, true: str) -> float:
        """ Computes TEDS score between the prediction and the ground truth of a given sample
        """
        if (not pred) or (not true):
            return 0.0
        parser = html.HTMLParser(remove_comments=True, encoding="utf-8")
        pred = html.fromstring(pred, parser=parser)
        true = html.fromstring(true, parser=parser)
        if pred.xpath("body/table") and true.xpath("body/table"):
            pred = pred.xpath("body/table")[0]
            true = true.xpath("body/table")[0]
            if self.ignore_nodes:
                etree.strip_tags(pred, *self.ignore_nodes)
                etree.strip_tags(true, *self.ignore_nodes)
            n_nodes_pred = len(pred.xpath(".//*"))
            n_nodes_true = len(true.xpath(".//*"))
            n_nodes = max(n_nodes_pred, n_nodes_true)
            tree_pred = self.load_html_tree(pred)
            tree_true = self.load_html_tree(true)

            distance = APTED(tree_pred, tree_true, CustomConfig()).compute_edit_distance()
            return 1.0 - (float(distance) / n_nodes)
        else:
            return 0.0

    def batch_evaluate(self, pred_json, true_json):
        """ Computes TEDS score between the prediction and the ground truth of
            a batch of samples
            @params pred_json: {'FILENAME': 'HTML CODE', ...}
            @params true_json: {'FILENAME': {'html': 'HTML CODE'}, ...}
            @output: {'FILENAME': 'TEDS SCORE', ...}
        """
        samples = true_json.keys()
        scores = [self.evaluate(pred_json.get(filename, "")["html"], true_json[filename]["html"]) for filename in tqdm(samples)]
        scores = dict(zip(samples, scores))
        return scores
