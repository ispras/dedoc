import os
from stat import S_IREAD, S_IRGRP, S_IROTH
from typing import List

from converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.utils import splitext_, get_file_mime_type


class FileConverterComposition(object):

    def __init__(self, converters: List[AbstractConverter]):
        self.converters = converters

    def do_converting(self, tmp_dir: str, filename: str) -> str:
        name, extension = splitext_(filename)
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))
        for converter in self.converters:
            if converter.can_convert(extension=extension, mime=mime):
                filename = converter.do_convert(tmp_dir, name, extension)
                break
        file_path = os.path.join(tmp_dir, filename)
        os.chmod(file_path, S_IREAD | S_IRGRP | S_IROTH)
        return filename
