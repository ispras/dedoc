from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class PDFConverter(AbstractConverter):
    """
    Converts pdf-like documents into PDF using the ddjvu application.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.timeout = 20

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is pdf-like, e.g. it has .djvu extension.
        """
        return extension.lower() in converted_extensions.pdf_like_format or mime in converted_mimes.pdf_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        Convert the pdf-like documents into files with .pdf extension using the ddjvu application.
        """
        path_in = f"{tmp_dir}/{filename}{extension}"
        expected_path = f"{tmp_dir}/{filename}.pdf"
        command = ["ddjvu", "--format=pdf", path_in, expected_path]
        self._run_subprocess(command=command, filename=filename, expected_path=expected_path)

        return filename + '.pdf'
