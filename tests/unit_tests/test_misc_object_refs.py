import unittest

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructors.concrete_structure_constructors.tree_constructor import TreeConstructor
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
from tests.test_utils import check_object_refs, collect_annotation_values, get_test_config


class TestObjectRefs(unittest.TestCase):

    def test_check_object_refs_accepts_matching_sets(self) -> None:
        errors = check_object_refs(["t1", "t2"], ["t2", "t1"], kind="table")
        self.assertEqual([], errors)

    def test_check_object_refs_rejects_dangling_annotation(self) -> None:
        errors = check_object_refs(["t1"], ["t1", "missing"], kind="table")
        self.assertEqual(["dangling table annotations: ['missing']"], errors)

    def test_check_object_refs_rejects_unlinked_object(self) -> None:
        errors = check_object_refs(["t1", "t2"], ["t1"], kind="table")
        self.assertEqual(["unlinked tables: ['t2']"], errors)

    def test_check_object_refs_allows_unlinked_when_not_required(self) -> None:
        errors = check_object_refs(["t1", "t2"], ["t1"], require_all_linked=False, kind="table")
        self.assertEqual([], errors)

    def test_check_object_refs_duplicate_uid_needs_one_to_one(self) -> None:
        object_uids = ["same", "same"]
        annotation_uids = ["same"]
        self.assertEqual([], check_object_refs(object_uids, annotation_uids, kind="table"))
        errors = check_object_refs(object_uids, annotation_uids, require_one_to_one=True, kind="table")
        self.assertEqual(1, len(errors))
        self.assertIn("uid counts differ", errors[0])

    def test_collect_annotation_values_from_api_tree(self) -> None:
        tree = {
            "annotations": [{"name": "table", "value": "t1"}],
            "metadata": {"page_id": 0, "line_id": 0},
            "subparagraphs": [{
                "annotations": [{"name": "attachment", "value": "a1"}, {"name": "bold", "value": "True"}],
                "metadata": {"page_id": 0, "line_id": 1},
                "subparagraphs": []
            }]
        }
        self.assertEqual(["t1"], collect_annotation_values(tree, "table"))
        self.assertEqual(["a1"], collect_annotation_values(tree, "attachment"))

    def test_pipeline_keeps_table_and_attach_refs_after_merge(self) -> None:
        """Two tables and two attachments on a glued raw_text line must stay linked after tree construction."""
        tables = [Table(cells=[], metadata=TableMetadata(page_id=0, uid="t1")), Table(cells=[], metadata=TableMetadata(page_id=0, uid="t2"))]
        attachments = [
            AttachedFile(original_name="a.png", tmp_file_path="/tmp/a.png", need_content_analysis=False, uid="a1"),
            AttachedFile(original_name="b.png", tmp_file_path="/tmp/b.png", need_content_analysis=False, uid="a2")
        ]
        first = LineWithMeta(line="Before ", metadata=LineMetadata(page_id=0, line_id=0))
        second = LineWithMeta(
            line="objects",
            metadata=LineMetadata(page_id=0, line_id=1),
            annotations=[
                TableAnnotation(value="t1", start=0, end=7),
                TableAnnotation(value="t2", start=0, end=7),
                AttachAnnotation(attach_uid="a1", start=0, end=7),
                AttachAnnotation(attach_uid="a2", start=0, end=7)
            ]
        )
        document = UnstructuredDocument(
            tables=tables,
            lines=[first, second],
            attachments=attachments,
            metadata={
                "file_name": "synthetic.txt",
                "temporary_file_name": "synthetic.txt",
                "size": 0,
                "modified_time": 0,
                "created_time": 0,
                "access_time": 0,
                "file_type": "text/plain"
            }
        )
        document = DefaultStructureExtractor(config=get_test_config()).extract(document)
        parsed = TreeConstructor().construct(document)

        table_anns = collect_annotation_values(parsed.content.structure, TableAnnotation.name)
        attach_anns = collect_annotation_values(parsed.content.structure, AttachAnnotation.name)
        table_uids = [table.metadata.uid for table in parsed.content.tables]
        attach_uids = [attachment.uid for attachment in document.attachments]

        self.assertEqual([], check_object_refs(table_uids, table_anns, require_one_to_one=True, kind="table"))
        self.assertEqual([], check_object_refs(attach_uids, attach_anns, require_one_to_one=True, kind="attachment"))
        self.assertEqual({"t1", "t2"}, set(table_anns))
        self.assertEqual({"a1", "a2"}, set(attach_anns))
