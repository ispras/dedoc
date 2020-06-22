from collections import OrderedDict
from typing import List, Iterable, Optional

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class TreeNode:

    def __init__(self,
                 node_id: str,
                 text: str,
                 annotations: List[Annotation],
                 metadata: ParagraphMetadata,
                 subparagraphs: List["TreeNode"],
                 hierarchy_level: HierarchyLevel,
                 parent: Optional["TreeNode"]):
        self.node_id = node_id
        self.text = text
        self.annotations = annotations
        self.metadata = metadata
        self.subparagraphs = subparagraphs
        self.hierarchy_level = hierarchy_level
        self.parent = parent

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["node_id"] = self.node_id
        res["text"] = self.text
        res["annotations"] = [annotation.to_dict() for annotation in self.annotations]
        res["metadata"] = self.metadata.to_dict()
        res["subparagraphs"] = [node.to_dict() for node in self.subparagraphs]
        return res

    @staticmethod
    def create(texts: Iterable[str]) -> "TreeNode":
        text = "\n".join(texts)
        metadata = ParagraphMetadata(paragraph_type="root", page_id=0, line_id=0, predicted_classes=None)
        hierarchy_level = HierarchyLevel(0, 0, True, paragraph_type="root")
        return TreeNode("0",
                        text,
                        annotations=[],
                        metadata=metadata,
                        subparagraphs=[],
                        hierarchy_level=hierarchy_level,
                        parent=None)

    def add_child(self, line: LineWithMeta) -> "TreeNode":
        new_node = TreeNode(
            node_id=self.node_id + ".{}".format(len(self.subparagraphs)),
            text=line.line,
            annotations=line.annotations,
            metadata=line.metadata,
            subparagraphs=[],
            hierarchy_level=line.hierarchy_level,
            parent=self
        )
        self.subparagraphs.append(new_node)
        return new_node

    def add_text(self, line: LineWithMeta):
        self.text = self.text + "\n"
        new_annotations = []
        text_length = len(self.text)
        for annotation in line.annotations:
            new_annotation = Annotation(start=annotation.start + text_length,
                                        end=annotation.end + text_length,
                                        value=annotation.value)
            new_annotations.append(new_annotation)
        self.text += line.line
        self.annotations.extend(new_annotations)

    def get_root(self):
        node = self
        while node.parent is not None:
            node = node.parent
        return node
