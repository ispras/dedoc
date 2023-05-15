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
    """
    This class is used for parsing documents with .xlsx extension.
    Please use :class:`~dedoc.converters.ExcelConverter` for getting xlsx file from similar formats.
    """
    def __init__(self) -> None:
        self.attachment_extractor = ExcelAttachmentsExtractor()

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return extension.lower() in recognized_extensions.excel_like_format or mime in recognized_mimes.excel_like_format

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        This method extracts tables and attachments from the document, `lines` attribute remains empty.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
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
