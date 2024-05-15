from typing import Optional

import xlrd
from xlrd.sheet import Sheet

from dedoc.attachments_extractors.concrete_attachments_extractors.excel_attachments_extractor import ExcelAttachmentsExtractor
from dedoc.data_structures import LineMetadata, LineWithMeta
from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.parameter_utils import get_param_with_attachments

xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True


class ExcelReader(BaseReader):
    """
    This class is used for parsing documents with .xlsx extension.
    Please use :class:`~dedoc.converters.ExcelConverter` for getting xlsx file from similar formats.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.excel_like_format, recognized_mimes=recognized_mimes.excel_like_format)
        self.attachment_extractor = ExcelAttachmentsExtractor(config=self.config)

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        This method extracts tables and attachments from the document, `lines` attribute remains empty.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        with xlrd.open_workbook(file_path) as book:
            sheets_num = book.nsheets
            tables = []
            for sheet_num in range(sheets_num):
                sheet = book.sheet_by_index(sheet_num)
                tables.append(self.__parse_sheet(sheet_num, sheet))
            if get_param_with_attachments(parameters):
                attachments = self.attachment_extractor.extract(file_path=file_path, parameters=parameters)
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
                row.append(CellWithMeta(lines=[LineWithMeta(line=value, metadata=LineMetadata(page_id=sheet_id, line_id=0))]))
            res.append(row)
        metadata = TableMetadata(page_id=sheet_id)
        return Table(cells=res, metadata=metadata)
