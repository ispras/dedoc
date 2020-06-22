import csv
from typing import Optional, Tuple

from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions
from dedoc.readers.base_reader import BaseReader


class CSVReader(BaseReader):
    # TODO inherit from reader
    def __init__(self):
        self.default_separator = ","

    def can_read(self, path: str, mime: str, extension: str, document_type: str) -> bool:
        return extension in recognized_extensions.csv_like_format

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:
        delimiter = parameters.get("delimiter")
        if delimiter is None:
            delimiter = "\t" if path.endswith(".tsv") else self.default_separator
        with open(path) as file:
            csv_reader = csv.reader(file, delimiter=delimiter)
            data = list(csv_reader)
        table_metadata = TableMetadata(page_id=0)
        tables = [Table(cells=data, metadata=table_metadata)]
        return UnstructuredDocument(lines=[], tables=tables), False
