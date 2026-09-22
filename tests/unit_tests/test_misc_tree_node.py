from unittest import TestCase

from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.tree_node import TreeNode
from dedoc.utils.annotation_merger import AnnotationMerger


class TestTreeNode(TestCase):

    def test_root_node_annotations(self) -> None:
        lines = [
            LineWithMeta(line="bold text\n",
                         metadata=LineMetadata(hierarchy_level=HierarchyLevel.create_root(), page_id=0, line_id=0),
                         annotations=[BoldAnnotation(start=0, end=10, value="True")]),
            LineWithMeta(line="italic text\n",
                         metadata=LineMetadata(hierarchy_level=HierarchyLevel.create_root(), page_id=0, line_id=1),
                         annotations=[ItalicAnnotation(start=0, end=12, value="True")]),
        ]

        node = TreeNode.create(lines=lines)
        node_annotations = node.get_root().annotations
        node_annotations.sort(key=lambda a: a.start)
        self.assertEqual(2, len(node_annotations))
        bold, italic = node_annotations
        self.assertEqual(BoldAnnotation.name, bold.name)
        self.assertEqual("True", bold.value)
        self.assertEqual(0, bold.start)
        self.assertEqual(10, bold.end)

        self.assertEqual(ItalicAnnotation.name, italic.name)
        self.assertEqual("True", italic.value)
        self.assertEqual(10, italic.start)
        self.assertEqual(22, italic.end)

    def test_add_text_keeps_multiple_tables_after_merge(self) -> None:
        """Two tables on a glued line must both survive add_text and AnnotationMerger."""
        hl = HierarchyLevel.create_raw_text()
        first = LineWithMeta(line="Начало ", metadata=LineMetadata(hierarchy_level=hl, page_id=0, line_id=0))
        tables = [TableAnnotation(value="t1", start=0, end=5), TableAnnotation(value="t2", start=0, end=5)]
        second = LineWithMeta(line="текст", metadata=LineMetadata(hierarchy_level=hl, page_id=0, line_id=1), annotations=tables)
        node = TreeNode.create(lines=[first])
        node.add_text(second)

        table_anns = [ann for ann in node.annotations if ann.name == TableAnnotation.name]
        self.assertEqual(2, len(table_anns))
        self.assertTrue(all(isinstance(ann, TableAnnotation) for ann in table_anns))
        self.assertTrue(all(ann.is_mergeable is False for ann in table_anns))

        merged = AnnotationMerger().merge_annotations(node.annotations, node.text)
        merged_tables = [ann for ann in merged if ann.name == TableAnnotation.name]
        self.assertEqual({"t1", "t2"}, {ann.value for ann in merged_tables})
