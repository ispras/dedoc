import csv
from typing import Optional, Tuple, List

from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_encoding


class CSVReader(BaseReader):
    """
    This class allows to parse files with the following extensions: .csv, .tsv.
    """
    def __init__(self) -> None:
        self.default_separator = ","

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return extension.lower() in recognized_extensions.csv_like_format

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method will place all extracted content inside tables of the :class:`~dedoc.data_structures.UnstructuredDocument`.
        The lines and attachments remain empty.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        delimiter = parameters.get("delimiter")
        if delimiter is None:
            delimiter = "\t" if path.endswith(".tsv") else self.default_separator
        encoding, encoding_warning = self.__get_encoding(path, parameters)
        with open(path, errors="ignore", encoding=encoding) as file:
            csv_reader = csv.reader(file, delimiter=delimiter)
            data = list(csv_reader)
        table_metadata = TableMetadata(page_id=0)
        tables = [Table(cells=data, metadata=table_metadata)]
        warnings = ["delimiter is '{}'".format(delimiter)]
        warnings.extend(encoding_warning)
        return UnstructuredDocument(lines=[], tables=tables, attachments=[], warnings=warnings)

    def __get_encoding(self, path: str, parameters: dict) -> Tuple[str, List[str]]:
        if parameters.get("encoding"):
            return parameters["encoding"], []
        else:
            encoding = get_encoding(path, "utf-8")
            return encoding, [f"encoding is {encoding}"]
