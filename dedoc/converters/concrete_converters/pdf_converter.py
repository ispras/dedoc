import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils.utils import splitext_


class PDFConverter(AbstractConverter):
    """
    Converts pdf-like documents (.djvu) into PDF using the ddjvu application.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, converted_extensions=converted_extensions.pdf_like_format, converted_mimes=converted_mimes.pdf_like_format)

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the pdf-like documents into files with .pdf extension using the ddjvu application.
        """
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, _ = splitext_(file_name)
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.pdf")
        command = ["ddjvu", "--format=pdf", file_path, converted_file_path]
        self._run_subprocess(command=command, filename=file_name, expected_path=converted_file_path)

        return converted_file_path
