import warnings
from collections import OrderedDict, defaultdict
from typing import List, Iterable, Optional, Dict
from flask_restx import fields, Api, Model

from dedoc.config import get_config
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.serializable import Serializable
from dedoc.structure_constructor.annotation_merger import AnnotationMerger
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
        :param node_id: node id is unique in one document
        :param text: text of node
        :param annotations: some metadata related to the part of the text (as font size)
        :param metadata: metadata refers to entire node (as node type)
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

    def to_dict(self, old_version: bool) -> dict:
        res = OrderedDict()
        res["node_id"] = self.node_id
        res["text"] = self.text
        res["annotations"] = [annotation.to_dict(old_version) for annotation in self.annotations]
        res["metadata"] = self.metadata.to_dict(old_version)
        res["subparagraphs"] = [node.to_dict(old_version) for node in self.subparagraphs]
        return res

    @staticmethod
    def get_api_dict(api: Api, depth: int = 0, name: str = 'TreeNode') -> Model:
        return api.model(name, {
            'node_id': fields.String(description="Document element identifier. It is unique within one tree (i.e. "
                                                 "there will be no other such node_id in this tree, but in attachment "
                                                 "it may occur) The identifier has the form 0.2.1 where each number "
                                                 "means a serial number at the corresponding level of the hierarchy.",
                                     required=True,
                                     example="0.2.1"
                                     ),
            'text': fields.String(description="text of node", required=True, example="Закон"),
            'annotations': fields.List(fields.Nested(Annotation.get_api_dict(api),
                                                     description="Text annotations "
                                                                 "(font, size, bold, italic and etc)")),
            'metadata': fields.Nested(ParagraphMetadata.get_api_dict(api),
                                      skip_none=True,
                                      allow_null=False,
                                      description="Paragraph meta information"),
            'subparagraphs': fields.List(fields.Nested(api.model('others_TreeNode', {})),
                                         description="Node childes (with type 'TreeNode') of structure tree")
            if depth == get_config()['recursion_deep_subparagraphs']
            else fields.List(fields.Nested(TreeNode.get_api_dict(api,
                                                                 depth=depth + 1,
                                                                 name='refTreeNode' + str(depth))),
                             description="Node childes (with type 'TreeNode') of structure tree")
        })

    @staticmethod
    def create(lines: List[LineWithMeta] = None) -> "TreeNode":
        """
        Creates a root node with given text
        :param lines: this lines should be the title of the document (or should be empty for documents without title)
        :return: root of the document tree
        """
        page_id = 0 if len(lines) == 0 else min((line.metadata.page_id for line in lines))
        line_id = 0 if len(lines) == 0 else min((line.metadata.line_id for line in lines))

        texts = (line.line for line in lines)
        annotations = []
        text_length = 0
        for line in lines:
            annotations.extend(TreeNode.__shift_annotations(line=line, text_length=text_length))
            text_length += len(line.line)
        text = "".join(texts)
        metadata = ParagraphMetadata(
            paragraph_type="root",
            page_id=page_id,
            line_id=line_id,
            predicted_classes=None)
        return TreeNode("0",
                        text,
                        annotations=annotations,
                        metadata=metadata,
                        subparagraphs=[],
                        hierarchy_level=HierarchyLevel.create_root(),
                        parent=None)

    def add_child(self, line: LineWithMeta) -> "TreeNode":
        """
        Create a new tree node - children of the given node from given line. Return newly created node
        :param line: Line with meta, new node will be built from this line
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
        add the text and annotations from given line, text is separated with \n
        :param line: line with text to add
        :return:
        """
        text_length = len(self.text)
        new_annotations = self.__shift_annotations(line, text_length)

        if self.text:
            self.text += '\n'

        self.text += line.line
        self.annotations.extend(new_annotations)

    @staticmethod
    def __shift_annotations(line: LineWithMeta, text_length: int) -> List[Annotation]:
        new_annotations = []
        for annotation in line.annotations:
            new_annotation = Annotation(start=annotation.start + text_length,
                                        end=annotation.end + text_length,
                                        name=annotation.name,
                                        value=annotation.value)
            new_annotations.append(new_annotation)
        return new_annotations

    def get_root(self):
        """
        :return: return root of the tree
        """
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def merge_annotations(self):
        root = self.get_root()
        stack = [root]
        merger = AnnotationMerger()
        while len(stack) > 0:
            node = stack.pop()
            node.annotations = merger.merge_annotations(node.annotations, node.text)
            for sub_node in node.subparagraphs:
                stack.append(sub_node)
