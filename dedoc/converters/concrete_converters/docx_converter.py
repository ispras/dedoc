import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils.utils import splitext_


class DocxConverter(AbstractConverter):
    """
    Converts docx-like documents (.doc, .rtf, .odt) into DOCX using the soffice application.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, converted_extensions=converted_extensions.docx_like_format, converted_mimes=converted_mimes.docx_like_format)

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the docx-like documents into files with .docx extension using the soffice application.
        """
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, _ = splitext_(file_name)
        command = ["soffice", "--headless", "--convert-to", "docx", "--outdir", file_dir, file_path]
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.docx")
        self._run_subprocess(command=command, filename=file_name, expected_path=converted_file_path)

        return converted_file_path
