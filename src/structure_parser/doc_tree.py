from collections import OrderedDict
from typing import List, Optional

from src.data_structures.line_with_meta import HierarchyLevel


class DocTree:

    def __init__(self, prefix: str,
                 hierarchy_level: Optional[HierarchyLevel],
                 parent: "DocTree",
                 child_num: int,
                 texts: List[str],
                 paragraph_type: Optional[dict]) -> None:
        self.prefix = prefix
        self._hierarchy_level = hierarchy_level
        self.parent = parent
        self.children = []
        self.child_num = child_num
        self.texts = texts
        self.key = prefix + "{}.".format(child_num)
        self.is_root = parent is None
        self.header = ""
        self.metainformation = paragraph_type

    @property
    def hierarchy_level(self) -> HierarchyLevel:
        return self._hierarchy_level

    @staticmethod
    def create(texts: Optional[List[str]] = None) -> "DocTree":
        if texts is None:
            texts = []
        return DocTree(prefix="",
                       hierarchy_level=(0, 0),
                       parent=None,
                       child_num=0,
                       texts=texts,
                       paragraph_type={"type": "root"}
                       )

    def add_text(self, text: str) -> None:
        self.texts.append(text)

    def add_child(self,
                  hierarchy_level: Optional[HierarchyLevel],
                  texts: List[str],
                  paragraph_type: Optional[dict]) -> "DocTree":

        if hierarchy_level is not None and self.hierarchy_level > hierarchy_level:
            raise ValueError("Child hierarchy level is {}, parent hierarchy level {}. Should be lower".format(
                hierarchy_level, self.hierarchy_level))

        child_prefix = self.key
        child = DocTree(prefix=child_prefix,
                        hierarchy_level=hierarchy_level,
                        parent=self,
                        child_num=len(self.children),
                        texts=texts,
                        paragraph_type=paragraph_type)

        self.children.append(child)
        return child

    def get_root(self) -> "DocTree":
        if self.parent is None:
            return self
        else:
            return self.parent.get_root()

    def as_dict(self) -> dict:  # we now pass header path from node to node from root to bottom
        res = OrderedDict()
        res["id"] = self.key
        res["header"] = self.header
        res["text"] = "\n".join(map(lambda s: s.rstrip("\n"), self.texts))
        res["metainformation"] = self.metainformation
        subparagraphs_key = "subparagraphs"

        res[subparagraphs_key] = [ch.as_dict() for ch in self.children]

        return res
