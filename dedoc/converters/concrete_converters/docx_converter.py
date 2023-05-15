import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_mimes, converted_extensions


class DocxConverter(AbstractConverter):
    """
    Converts docx-like documents into DOCX using the soffice application.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is docx-like, e.g. it has .doc or .odt extension.
        """
        return extension.lower() in converted_extensions.docx_like_format or mime in converted_mimes.docx_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        Convert the docx-like documents into files with .docx extension using the soffice application.
        """
        path_in = f"{tmp_dir}/{filename}{extension}"
        command = ["soffice", "--headless", "--convert-to", "docx", "--outdir", tmp_dir, path_in]
        file_out = filename + ".docx"
        expected_path = os.path.join(tmp_dir, file_out)
        self._run_subprocess(command=command, filename=filename, expected_path=expected_path)

        return file_out
