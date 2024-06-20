from typing import List, Optional, Tuple

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader


class CSVReader(BaseReader):
    """
    This class allows to parse files with the following extensions: .csv, .tsv.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        super().__init__(config=config, recognized_extensions=recognized_extensions.csv_like_format, recognized_mimes=recognized_mimes.csv_like_format)
        self.default_separator = ","

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method will place all extracted content inside tables of the :class:`~dedoc.data_structures.UnstructuredDocument`.
        The lines and attachments remain empty.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        import pandas as pd
        from dedoc.data_structures.line_metadata import LineMetadata
        from dedoc.data_structures.line_with_meta import LineWithMeta
        from dedoc.data_structures.cell_with_meta import CellWithMeta
        from dedoc.data_structures.table import Table
        from dedoc.data_structures.table_metadata import TableMetadata

        parameters = {} if parameters is None else parameters
        delimiter = parameters.get("delimiter")
        if delimiter is None:
            delimiter = "\t" if file_path.endswith(".tsv") else self.default_separator
        encoding, encoding_warning = self.__get_encoding(file_path, parameters)
        df = pd.read_csv(file_path, sep=delimiter, header=None, encoding=encoding, dtype="string", keep_default_na=False)
        table_metadata = TableMetadata(page_id=0)
        cells_with_meta = []
        line_id = 0
        for ind in df.index:
            row_lines = []
            for cell in df.loc[ind]:
                row_lines.append(CellWithMeta(lines=[LineWithMeta(line=cell, metadata=LineMetadata(page_id=0, line_id=line_id))]))
                line_id += 1
            cells_with_meta.append(row_lines)

        tables = [Table(cells=cells_with_meta, metadata=table_metadata)]
        warnings = [f"delimiter is '{delimiter}'"]
        warnings.extend(encoding_warning)
        return UnstructuredDocument(lines=[], tables=tables, attachments=[], warnings=warnings)

    def __get_encoding(self, path: str, parameters: dict) -> Tuple[str, List[str]]:
        from dedoc.utils.utils import get_encoding

        if parameters.get("encoding"):
            return parameters["encoding"], []
        else:
            encoding = get_encoding(path, "utf-8")
            return encoding, [f"encoding is {encoding}"]
