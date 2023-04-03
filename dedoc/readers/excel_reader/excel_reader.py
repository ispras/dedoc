import os
from typing import Optional
import xlrd
from xlrd.sheet import Sheet

from dedoc.attachments_extractors.concrete_attachments_extractors.excel_attachments_extractor import ExcelAttachmentsExtractor
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader

xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True


class ExcelReader(BaseReader):

    def __init__(self, *, config: dict) -> None:
        self.attachment_extractor = ExcelAttachmentsExtractor()

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: Optional[str],
                 parameters: Optional[dict] = None) -> bool:
        return extension.lower() in recognized_extensions.excel_like_format or mime in recognized_mimes.excel_like_format

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> UnstructuredDocument:
        parameters = {} if parameters is None else parameters
        with xlrd.open_workbook(path) as book:
            sheets_num = book.nsheets
            tables = []
            for sheet_num in range(sheets_num):
                sheet = book.sheet_by_index(sheet_num)
                tables.append(self.__parse_sheet(sheet_num, sheet))
            if self.attachment_extractor.with_attachments(parameters=parameters):
                attachments = self.attachment_extractor.get_attachments(tmpdir=os.path.dirname(path),
                                                                        filename=os.path.basename(path),
                                                                        parameters=parameters)
            else:
                attachments = []
            return UnstructuredDocument(lines=[], tables=tables, attachments=attachments, warnings=[])

    def __parse_sheet(self, sheet_id: int, sheet: Sheet) -> Table:
        n_rows = sheet.nrows
        n_cols = sheet.ncols
        res = []
        for row_id in range(n_rows):
            row = []
            for col_id in range(n_cols):
                value = str(sheet.cell_value(rowx=row_id, colx=col_id))
                row.append(value)
            res.append(row)
        metadata = TableMetadata(page_id=sheet_id)
        return Table(cells=res, metadata=metadata)
