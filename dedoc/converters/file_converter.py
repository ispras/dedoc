import inspect
import os
import warnings
from stat import S_IREAD, S_IRGRP, S_IROTH
from typing import List, Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.utils.utils import splitext_, get_file_mime_type


class FileConverterComposition(object):
    """
    This class allows to convert any document into the predefined list of formats according to the available list of converters.
    The list of converters is set via the class constructor.
    The first suitable converter is used (the one whose method :meth:`~dedoc.converters.AbstractConverter.can_convert` returns True), \
    so the order of converters is important.
    """
    def __init__(self, converters: List[AbstractConverter]) -> None:
        """
        :param converters: the list of converters that have methods can_convert() and do_convert(), \
        they are used for files converting into specified formats
        """
        self.converters = converters

    def do_converting(self, tmp_dir: str, filename: str, parameters: Optional[dict] = None) -> str:
        """
        Convert file if there is the converter that can do it.
        If there isn't any converter that is able to convert the file, it isn't changed.

        :param tmp_dir: the directory where the file is located and where the converted file will be saved
        :param filename: the name of the file to convert
        :param parameters: parameters of converting
        :return: name of the converted file if conversion was executed else name of the original file
        """
        name, extension = splitext_(filename)
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))
        for converter in self.converters:
            if "parameters" in inspect.getfullargspec(converter.can_convert).args:
                can_convert = converter.can_convert(extension=extension, mime=mime, parameters=parameters)
            else:
                warnings.warn("!WARNING! you converter requires an update\n" +
                              "Please specify parameters argument in method can_convert in {}\n".format(type(converter).__name__) +
                              " These parameters would be mandatory in the near future")
                can_convert = converter.can_convert(extension=extension, mime=mime)
            if can_convert:
                filename = converter.do_convert(tmp_dir, name, extension)
                break
        file_path = os.path.join(tmp_dir, filename)
        os.chmod(file_path, S_IREAD | S_IRGRP | S_IROTH)
        return filename
