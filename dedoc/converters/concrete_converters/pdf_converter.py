from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class PDFConverter(AbstractConverter):
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.timeout = 20

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return extension.lower() in converted_extensions.pdf_like_format or mime in converted_mimes.pdf_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        path_in = "{tmp_dir}/{filename}{extension}".format(tmp_dir=tmp_dir, extension=extension, filename=filename)
        expected_path = "{tmp_dir}/{filename}.pdf".format(tmp_dir=tmp_dir, filename=filename)
        command = ["ddjvu", "--format=pdf", path_in, expected_path]
        self._run_subprocess(command=command, filename=filename, expected_path=expected_path)

        return filename + '.pdf'
