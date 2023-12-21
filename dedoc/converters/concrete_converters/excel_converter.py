import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils.utils import get_mime_extension, splitext_


class ExcelConverter(AbstractConverter):
    """
    Converts xlsx-like documents into XLSX using the soffice application.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def can_convert(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is xlsx-like, e.g. it has .xls or .ods extension.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in converted_extensions.excel_like_format or mime in converted_mimes.excel_like_format

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the xlsx-like documents into files with .xlsx extension using the soffice application.
        """
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, _ = splitext_(file_name)
        command = ["soffice", "--headless", "--convert-to", "xlsx", "--outdir", file_dir, file_path]
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.xlsx")
        self._run_subprocess(command=command, filename=file_name, expected_path=converted_file_path)

        return converted_file_path
