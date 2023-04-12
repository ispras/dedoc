from typing import List

from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata


class TablePatcher:
    """
    this class copy table information from table to the structure (document tree),
    it is not copy table if it marked as already in the document tree.
    """

    def insert_table(self, document: UnstructuredDocument) -> UnstructuredDocument:
        """
        takes a document as the input and insert table cells into the paragraphs list.
        Does not insert table if it already was inserted
        """
        tables_dict = {table.metadata.uid: table for table in document.tables if not table.metadata.is_inserted}
        paragraphs = []
        hierarchy_level = max((line.metadata.hierarchy_level.level_1 for line in document.lines
                               if not line.metadata.hierarchy_level.is_raw_text()), default=0)
        for line in document.lines:
            if line.metadata.hierarchy_level.is_raw_text():
                hierarchy_level_raw_text = HierarchyLevel(level_1=hierarchy_level + 1,
                                                          level_2=0,
                                                          can_be_multiline=line.metadata.hierarchy_level.can_be_multiline,
                                                          line_type=HierarchyLevel.raw_text)
                line.metadata.hierarchy_level = hierarchy_level_raw_text
            paragraphs.append(line)
            for annotation in line.annotations:
                if annotation.name == TableAnnotation.name:
                    table_id = annotation.value
                    if table_id in tables_dict:
                        table = tables_dict[table_id]
                        paragraphs += self._create_paragraphs_from_table(table=table, hierarchy_level=hierarchy_level)
                        tables_dict.pop(table_id)
        for table in tables_dict.values():
            paragraphs += self._create_paragraphs_from_table(table=table, hierarchy_level=hierarchy_level)
        return UnstructuredDocument(lines=paragraphs,
                                    tables=document.tables,
                                    attachments=document.attachments,
                                    warnings=document.warnings,
                                    metadata=document.metadata)

    def _create_paragraphs_from_table(self, table: Table, hierarchy_level: int) -> List[LineWithMeta]:
        """
        create lines with meta from table to insert it after the given line
        """
        table.metadata.is_inserted = True
        table_line = self._create_table_line(table=table, hierarchy_level=hierarchy_level)
        result = [table_line]
        for row in table.cells:
            result.append(self._create_row_line(table=table, hierarchy_level=hierarchy_level))
            for cell in row:
                result.append(self._create_cell_line(table=table, hierarchy_level=hierarchy_level, cell=cell))
        return result

    @staticmethod
    def _create_table_line(table: Table, hierarchy_level: int) -> LineWithMeta:
        hierarchy_level_new = HierarchyLevel(
            level_1=hierarchy_level + 2,  # table hierarchy is lower than raw text
            level_2=0,
            can_be_multiline=False,
            line_type="table"
        )
        metadata = LineMetadata(hierarchy_level=hierarchy_level_new, page_id=table.metadata.page_id, line_id=None)
        return LineWithMeta(line="", metadata=metadata, annotations=[], uid="table_{}".format(table.metadata.uid))

    @staticmethod
    def _create_row_line(table: Table, hierarchy_level: int) -> LineWithMeta:
        hierarchy_level_new = HierarchyLevel(
            level_1=hierarchy_level + 3,
            level_2=0,
            can_be_multiline=False,
            line_type="table_row"
        )
        metadata = LineMetadata(hierarchy_level=hierarchy_level_new, page_id=table.metadata.page_id, line_id=None)
        return LineWithMeta(line="", metadata=metadata, annotations=[])

    @staticmethod
    def _create_cell_line(table: Table, hierarchy_level: int, cell: str) -> LineWithMeta:
        hierarchy_level_new = HierarchyLevel(
            level_1=hierarchy_level + 4,
            level_2=0,
            can_be_multiline=False,
            line_type="table_cell"
        )
        metadata = LineMetadata(hierarchy_level=hierarchy_level_new, page_id=table.metadata.page_id, line_id=None)
        return LineWithMeta(line=cell, metadata=metadata, annotations=[])
