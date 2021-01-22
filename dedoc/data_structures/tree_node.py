import warnings
from collections import OrderedDict, defaultdict
from typing import List, Iterable, Optional, Dict
from flask_restx import fields, Api, Model

from dedoc.config import get_config
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.serializable import Serializable
from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.utils import special_match


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
    def create(lines: List[LineWithMeta] = None, texts: Iterable[str] = None) -> "TreeNode":
        """
        Creates a root node with given text
        :param lines: this lines should be the title of the document (or should be empty for documents without title)
        :param texts: deprecated, use lines instead
        :return: root of the document tree
        """
        if texts is None and lines is None:
            raise ValueError("You should specify lines")
        elif texts is not None and lines is not None:
            warnings.warn("specify only lines, texts ignored")
        elif texts is not None and lines is None:
            warnings.warn("texts is deprecated and would be removed soon, use lines")
            lines = [LineWithMeta(line=text, metadata=ParagraphMetadata(
                line_id=0,
                paragraph_type="",
                page_id=0,
                predicted_classes=None
            ), hierarchy_level=None, annotations=[]) for text in texts]

        page_id = 0 if len(lines) == 0 else min((line.metadata.page_id for line in lines))
        line_id = 0 if len(lines) == 0 else min((line.metadata.line_id for line in lines))

        texts = (line.line for line in lines)
        text = "".join(texts)
        metadata = ParagraphMetadata(
            paragraph_type="root",
            page_id=page_id,
            line_id=line_id,
            predicted_classes=None)
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
        new_annotations = []
        text_length = len(self.text)
        for annotation in line.annotations:
            new_annotation = Annotation(start=annotation.start + text_length - 1,
                                        end=annotation.end + text_length,
                                        name=annotation.name,
                                        value=annotation.value)
            new_annotations.append(new_annotation)
        self.text += line.line
        self.annotations.extend(new_annotations)
        self.annotations = self._merge_annotations(self.annotations, self.text)

    def get_root(self):
        """
        :return: return root of the tree
        """
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @staticmethod
    def _group_annotations(annotations: List[Annotation]) -> Dict[str, List[Annotation]]:
        annotations_group_by_value = defaultdict(list)
        for annotation in annotations:
            annotations_group_by_value[(annotation.name, annotation.value)].append(annotation)
        return annotations_group_by_value

    @staticmethod
    def _merge_annotations(annotations: List[Annotation], text: str) -> List[Annotation]:
        has_merged = False
        deep = 1
        while not has_merged:
            annotations, has_merged = TreeNode._merge_annotations_on_one_level(annotations, text)
            deep += 1

        return annotations

    @staticmethod
    def delete_previous_merged(merged: List[Annotation], new_annotations: Annotation) -> List[Annotation]:
        """
            Deleting previous merged annotations which have become unactual with the new merged annotation
        """
        deleted_list = []
        for annotation in merged:
            if annotation.start == new_annotations.start and \
                    annotation.name == new_annotations.name and \
                    annotation.value == new_annotations.value and \
                    annotation.end <= new_annotations.end:
                deleted_list.append(annotation)

        for annotation in deleted_list:
            merged.remove(annotation)

        return merged

    @staticmethod
    def _merge_annotations_on_one_level(annotations: List[Annotation], text: str) -> [List[Annotation], bool]:
        """
        Merge annotations when end of the firs annotation and start of the second match and has same value.
        Used with add_text
        """
        annotations_group_by_name_value = TreeNode._group_annotations(annotations).values()

        merged_set = set()
        merged = []
        for annotation_group in annotations_group_by_name_value:
            for num_first, first_annotation in enumerate(annotation_group):
                for num_second, second_annotation in enumerate(annotation_group):

                    if num_first >= num_second:
                        continue

                    if first_annotation.end >= second_annotation.start \
                            and first_annotation.start < second_annotation.end or \
                            (first_annotation.end < second_annotation.start and
                             special_match(text[first_annotation.end: second_annotation.start], r'[^.?!,:;"\'\n\r ]')):
                        merged_annotation = Annotation(start=min(first_annotation.start, second_annotation.start),
                                                       end=max(first_annotation.end, second_annotation.end),
                                                       name=first_annotation.name,
                                                       value=first_annotation.value)

                        merged = TreeNode.delete_previous_merged(merged, merged_annotation)
                        merged.append(merged_annotation)

                        merged_set.add((first_annotation.end, first_annotation.start,
                                        first_annotation.name, first_annotation.value))
                        merged_set.add((second_annotation.end, second_annotation.start,
                                        second_annotation.name, second_annotation.value))

        other_annotations = [annotation for annotation in annotations
                             if (annotation.end, annotation.start, annotation.name, annotation.value) not in merged_set]

        return sorted(other_annotations + merged, key=lambda a: a.start), len(merged) == 0
