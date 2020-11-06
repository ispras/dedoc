import os

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_mimes, converted_extensions


class DocxConverter(AbstractConverter):
    def __init__(self):
        super().__init__()

    def can_convert(self, extension: str, mime: str) -> bool:
        return extension in converted_extensions.docx_like_format or mime in converted_mimes.docx_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        os.system("soffice --headless --convert-to docx --outdir {tmp_dir} {tmp_dir}/{filename}{extension}".format(
            tmp_dir=tmp_dir, filename=filename, extension=extension
        ))
        self._await_for_conversion(filename + '.docx', tmp_dir)

        return filename + '.docx'
