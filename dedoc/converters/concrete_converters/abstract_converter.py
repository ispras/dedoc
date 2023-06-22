import logging
import os
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Optional, List

from dedoc.common.exceptions.conversion_exception import ConversionException


class AbstractConverter(ABC):
    """
    This class provides the common methods for all converters: can_convert() and do_convert().
    """
    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the converter, e.g. logger for logging
        """
        self.timeout = 10
        self.period_checking = 0.05
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    @abstractmethod
    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        Convert the given file to another format if it's possible.
        This method can only be called on appropriate files, ensure that :meth:`~dedoc.converters.AbstractConverter.can_convert` \
        is True for the given file.
        If the file format is unsupported the ConversionException will be thrown.

        :param tmp_dir: directory where the original file is located and where result will be saved
        :param filename: name of the original file without extension
        :param extension: extension of the original file
        :return: name of the converted file
        """
        pass

    @abstractmethod
    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Check if this converter can convert file with the given extension.

        :param extension: file extension, for example .doc or .pdf
        :param mime: MIME type of file
        :param parameters: any additional parameters for given document
        :return: the indicator of possibility to convert this file
        """

    def _run_subprocess(self, command: List[str], filename: str, expected_path: str) -> None:
        try:
            conversion_results = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=self.timeout)
            error_message = conversion_results.stderr.decode().strip()
            if len(error_message) > 0:
                if os.path.isfile(expected_path):
                    self.logger.warning(f"Warning on file {filename}\n{error_message}")
                else:
                    error_message = f"Could not convert file {filename}\n{error_message}"
                    self.logger.error(error_message)
                    raise ConversionException(msg=error_message)

        except subprocess.TimeoutExpired:
            message = f"Conversion of the {filename} hadn't terminated after {self.timeout} seconds"
            self.logger.error(message)
            raise ConversionException(msg=message)

    def _await_for_conversion(self, filename: str, tmp_dir: str) -> None:
        t = 0
        while (not os.path.isfile(f"{tmp_dir}/{filename}")) and (t < self.timeout):
            time.sleep(self.period_checking)
            t += self.period_checking

            if t >= self.timeout:
                raise ConversionException(msg=f"fail with {tmp_dir}/{filename}", msg_api=f"Unsupported file format {filename}")
