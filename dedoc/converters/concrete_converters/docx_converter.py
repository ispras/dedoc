import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_mimes, converted_extensions


class DocxConverter(AbstractConverter):
    def __init__(self, *, config: dict):
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return extension in converted_extensions.docx_like_format or mime in converted_mimes.docx_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:

        path_in = "{tmp_dir}/{filename}{extension}".format(tmp_dir=tmp_dir, extension=extension, filename=filename)
        command = ["soffice", "--headless", "--convert-to", "docx", "--outdir", tmp_dir, path_in]
        expected_path = os.path.join(tmp_dir, filename + ".docx")
        self._run_subprocess(command=command, filename=filename, expected_path=expected_path)

        return filename + '.docx'
