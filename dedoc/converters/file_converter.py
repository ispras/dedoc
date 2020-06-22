import os
from typing import List

from dedoc.converters.base_converter import BaseConverter
from dedoc.utils import splitext_, get_file_mime_type


class FileConverter(object):

    def __init__(self, converters: List[BaseConverter]):
        self.converters = converters

    def do_converting(self, tmp_dir: str, filename: str):
        name, extension = splitext_(filename)
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))
        for converter in self.converters:
            if converter.can_convert(extension=extension, mime=mime):
                return converter.do_convert(tmp_dir, name, extension)
        return filename
