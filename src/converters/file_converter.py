import inspect
import os
import warnings
from stat import S_IREAD, S_IRGRP, S_IROTH
from typing import List, Optional

from src.converters.concrete_converters.abstract_converter import AbstractConverter
from src.utils.utils import splitext_, get_file_mime_type


class FileConverterComposition(object):

    def __init__(self, converters: List[AbstractConverter]) -> None:
        self.converters = converters

    def do_converting(self, tmp_dir: str, filename: str, parameters: Optional[dict] = None) -> str:
        name, extension = splitext_(filename)
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))
        for converter in self.converters:
            if "parameters" in inspect.getfullargspec(converter.can_convert).args:
                can_convert = converter.can_convert(extension=extension, mime=mime, parameters=parameters)
            else:
                warnings.warn("!WARNING! you converter requires an update\n" +
                              "Please specify parameters argument in method can_convert in {}\n".format(
                                  type(converter).__name__) +
                              " This parameters would be mandatory in the near future")
                can_convert = converter.can_convert(extension=extension, mime=mime)
            if can_convert:
                filename = converter.do_convert(tmp_dir, name, extension)
                break
        file_path = os.path.join(tmp_dir, filename)
        os.chmod(file_path, S_IREAD | S_IRGRP | S_IROTH)
        return filename
