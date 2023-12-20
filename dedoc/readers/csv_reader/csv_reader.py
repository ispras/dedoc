import csv
from typing import List, Optional, Tuple

from dedoc.data_structures import LineMetadata, LineWithMeta
from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_encoding, get_mime_extension


class CSVReader(BaseReader):
    """
    This class allows to parse files with the following extensions: .csv, .tsv.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.default_separator = ","

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in recognized_extensions.csv_like_format

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method will place all extracted content inside tables of the :class:`~dedoc.data_structures.UnstructuredDocument`.
        The lines and attachments remain empty.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        delimiter = parameters.get("delimiter")
        if delimiter is None:
            delimiter = "\t" if file_path.endswith(".tsv") else self.default_separator
        encoding, encoding_warning = self.__get_encoding(file_path, parameters)
        with open(file_path, errors="ignore", encoding=encoding) as file:
            csv_reader = csv.reader(file, delimiter=delimiter)
            data = list(csv_reader)
        table_metadata = TableMetadata(page_id=0)
        cells_with_meta = []
        line_id = 0
        for row in data:
            row_lines = []
            for cell in row:
                row_lines.append(CellWithMeta(lines=[LineWithMeta(line=cell, metadata=LineMetadata(page_id=0, line_id=line_id))]))
                line_id += 1
            cells_with_meta.append(row_lines)

        tables = [Table(cells=cells_with_meta, metadata=table_metadata)]
        warnings = [f"delimiter is '{delimiter}'"]
        warnings.extend(encoding_warning)
        return UnstructuredDocument(lines=[], tables=tables, attachments=[], warnings=warnings)

    def __get_encoding(self, path: str, parameters: dict) -> Tuple[str, List[str]]:
        if parameters.get("encoding"):
            return parameters["encoding"], []
        else:
            encoding = get_encoding(path, "utf-8")
            return encoding, [f"encoding is {encoding}"]
