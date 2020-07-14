from collections import OrderedDict
from typing import List, Iterable, Optional

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.serializable import Serializable
from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class TreeNode(Serializable):

    def __init__(self,
                 node_id: str,
                 text: str,
                 annotations: List[Annotation],
                 metadata: ParagraphMetadata,
                 subparagraphs: List["TreeNode"],
                 hierarchy_level: HierarchyLevel,
                 parent: Optional["TreeNode"]):
        """
        TreeNode helps to represent document as recursive tree structure. It has parent node (None for root ot the tree)
        and list of children nodes (empty list for list node)
        :param node_id: node id unique in one document
        :param text: text of node
        :param annotations: some metadata related to the part of the text (as font size)
        :param metadata: metadata related to all node (as node type)
        :param subparagraphs: list of child of this node
        :param hierarchy_level: helps to define the position of this node in the document tree
        :param parent: parent node (None for root, not none for other nodes)
        """
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
        """
        Create root node with given text
        :param texts: this text should be the title of the document (or should be empty for documents without title)
        :return: root of the document tree
        """
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
        """
        Create new tree node - children of the given node from given line. Return newly created node
        :param line: Line with meta, new node will be build from this line
        :return: return created node (child of the self)
        """
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
        """
        add text and annotations from given line, text separated with \n
        :param line: line with text to add
        :return:
        """
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
        """
        :return: return root of the tree
        """
        node = self
        while node.parent is not None:
            node = node.parent
        return node
