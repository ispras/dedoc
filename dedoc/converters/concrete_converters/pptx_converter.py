import os

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class PptxConverter(AbstractConverter):
    def __init__(self):
        super().__init__()

    def can_convert(self, extension: str, mime: str) -> bool:
        return extension in converted_extensions.pptx_like_format or mime in converted_mimes.pptx_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        os.system("soffice --headless --convert-to pptx --outdir {tmp_dir} {tmp_dir}/{filename}{extension}".format(
            tmp_dir=tmp_dir, filename=filename, extension=extension
        ))
        self._await_for_conversion(filename + '.pptx', tmp_dir)

        return filename + '.pptx'
