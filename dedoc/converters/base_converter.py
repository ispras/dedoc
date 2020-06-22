import os
import time
from abc import ABC, abstractmethod

from dedoc.common.exceptions.conversion_exception import ConversionException


class BaseConverter(ABC):
    def __init__(self):
        self.timeout = 10
        self.period_checking = 0.05

    @abstractmethod
    def do_convert(self, tmp_dir: str, name: str, extension: str) -> str:
        """
        take into input some file and convert it to other format (if necessary)
        :param tmp_dir: directory where lay original file and where result will be saved
        :param name: name of the original file
        :param extension: extension of the original file
        :return: name of the converted file
        """
        pass

    @abstractmethod
    def can_convert(self, extension: str, mime: str) -> bool:
        """
        check if this converter can convert file with given extension
        :param extension: file extension, for example .doc or .pdf
        :param mime: MIME type of a file
        :return:
        """

    def _await_for_conversion(self, filename: str, tmp_dir: str):
        t = 0
        while (not os.path.isfile("{tmp_dir}/{filename}".format(tmp_dir=tmp_dir, filename=filename))) \
                and (t < self.timeout):
            time.sleep(self.period_checking)
            t += self.period_checking

            if t >= self.timeout:
                raise ConversionException("fail with {tmp_dir}/{filename}".format(tmp_dir=tmp_dir, filename=filename))
