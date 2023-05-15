import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class ExcelConverter(AbstractConverter):
    """
    Converts xlsx-like documents into XLSX using the soffice application.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is xlsx-like, e.g. it has .xls or .ods extension.
        """
        return extension.lower() in converted_extensions.excel_like_format or mime in converted_mimes.excel_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        Convert the xlsx-like documents into files with .xlsx extension using the soffice application.
        """
        path_in = f"{tmp_dir}/{filename}{extension}"
        command = ["soffice", "--headless", "--convert-to", "xlsx", "--outdir", tmp_dir, path_in]
        file_out = filename + '.xlsx'
        expected_path = os.path.join(tmp_dir, file_out)
        self._run_subprocess(command=command, filename=filename, expected_path=expected_path)

        return file_out
