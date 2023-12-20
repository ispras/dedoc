import os
from stat import S_IREAD, S_IRGRP, S_IROTH
from typing import List, Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.utils.utils import get_mime_extension


class ConverterComposition(object):
    """
    This class allows to convert any document into the predefined list of formats according to the available list of converters.
    The list of converters is set via the class constructor.
    The first suitable converter is used (the one whose method :meth:`~dedoc.converters.AbstractConverter.can_convert` returns True), \
    so the order of converters is important.
    """
    def __init__(self, converters: List[AbstractConverter]) -> None:
        """
        :param converters: the list of converters that have methods can_convert() and convert(), \
        they are used for files converting into specified formats
        """
        self.converters = converters

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert file if there is the converter that can do it.
        If there isn't any converter that is able to convert the file, it isn't changed.

        :param file_path: path of the file to convert
        :param parameters: parameters of converting, see :ref:`parameters_description` for more details
        :return: path of converted file if conversion was executed else path of the original file
        """
        extension, mime = get_mime_extension(file_path=file_path)
        converted_file_path = file_path

        for converter in self.converters:
            if converter.can_convert(file_path=file_path, extension=extension, mime=mime, parameters=parameters):
                converted_file_path = converter.convert(file_path, parameters=parameters)
                break
        os.chmod(converted_file_path, S_IREAD | S_IRGRP | S_IROTH)
        return converted_file_path
