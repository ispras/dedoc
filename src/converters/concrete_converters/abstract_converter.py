import logging
import os
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Optional, List

from src.common.exceptions.conversion_exception import ConversionException


class AbstractConverter(ABC):
    def __init__(self, *, config: dict) -> None:
        self.timeout = 10
        self.period_checking = 0.05
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    @abstractmethod
    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        take into input some file and convert it to other format (if necessary)
        :param tmp_dir: directory where lay original file and where result will be saved
        :param filename: name of the original file
        :param extension: extension of the original file
        :return: name of the converted file
        """
        pass

    @abstractmethod
    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        check if this converter can convert file with given extension
        :param extension: file extension, for example .doc or .pdf
        :param mime: MIME type of a file
        :param parameters: any additional parameters for given document
        :return:
        """

    def _run_subprocess(self, command: List[str], filename: str, expected_path: str) -> None:
        try:
            conversion_results = subprocess.run(command,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                timeout=self.timeout)
            error_message = conversion_results.stderr.decode().strip()
            if len(error_message) > 0:
                if os.path.isfile(expected_path):
                    error_message = "Warning on file {} \n".format(filename) + error_message
                    self.logger.warning(error_message)
                else:
                    error_message = "Could not convert file {} \n".format(filename) + error_message
                    self.logger.error(error_message)
                    raise ConversionException(msg=error_message)

        except subprocess.TimeoutExpired:
            message = "Conversion of the {} hadn't terminated after {} seconds".format(filename, self.timeout)
            self.logger.error(message)
            raise ConversionException(msg=message)

    def _await_for_conversion(self, filename: str, tmp_dir: str) -> None:
        t = 0
        while (not os.path.isfile("{tmp_dir}/{filename}".format(tmp_dir=tmp_dir, filename=filename))) \
                and (t < self.timeout):
            time.sleep(self.period_checking)
            t += self.period_checking

            if t >= self.timeout:
                raise ConversionException(msg="fail with {tmp_dir}/{filename}".format(tmp_dir=tmp_dir, filename=filename),
                                          msg_api="Unsupported file format {}".format(filename))
