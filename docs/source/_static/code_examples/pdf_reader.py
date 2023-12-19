from typing import List, Optional

import tabula
from PyPDF2 import PdfFileReader
from pdf_attachment_extractor import PdfAttachmentsExtractor

from dedoc.data_structures import CellWithMeta, LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_mime_extension


class PdfReader(BaseReader):

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.attachment_extractor = PdfAttachmentsExtractor(config=self.config)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension in recognized_extensions.pdf_like_format or mime in recognized_mimes.pdf_like_format

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        parameters = {} if parameters is None else parameters
        lines = self.__process_lines(file_path)
        tables = self.__process_tables(file_path)
        attachments = self.attachment_extractor.extract(file_path=file_path, parameters=parameters)
        return UnstructuredDocument(lines=lines, tables=tables, attachments=attachments)

    def __process_tables(self, path: str) -> List[Table]:
        dfs = tabula.read_pdf(path, stream=True, pages="all")
        tables = []
        for df in dfs:
            metadata = TableMetadata(page_id=None)
            cells = [[CellWithMeta(lines=[LineWithMeta(line=text_cell)]) for text_cell in row]for row in df.values.tolist()]
            tables.append(Table(cells=cells, metadata=metadata))
        return tables

    def __process_lines(self, path: str) -> List[LineWithMeta]:
        with open(path, "rb") as file:
            lines_with_meta = []
            pdf = PdfFileReader(file)
            num_pages = pdf.getNumPages()
            for page_id in range(num_pages):
                page = pdf.getPage(page_id)
                text = page.extractText()
                lines = text.split("\n")
                for line_id, line in enumerate(lines):
                    metadata = LineMetadata(page_id=page_id, line_id=line_id)
                    lines_with_meta.append(LineWithMeta(line=line, metadata=metadata, annotations=[]))
        return lines_with_meta
