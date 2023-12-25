import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional

from dedoc.common.exceptions.conversion_error import ConversionError


class AbstractConverter(ABC):
    """
    This class provides the common methods for all converters: can_convert() and convert().
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        """
        :param config: configuration of the converter, e.g. logger for logging
        """
        self.timeout = 60
        self.period_checking = 0.05
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())

    @abstractmethod
    def can_convert(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        """
        Check if this converter can convert file.
        You should provide at least one of the following parameters: file_path, extension, mime.

        :param file_path: path of the file to convert
        :param extension: file extension, for example .doc or .pdf
        :param mime: MIME type of file
        :param parameters: any additional parameters for the given document
        :return: the indicator of possibility to convert this file
        """
        pass

    @abstractmethod
    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the given file to another format if it's possible.
        This method can only be called on appropriate files, ensure that :meth:`~dedoc.converters.AbstractConverter.can_convert` \
        is True for the given file.
        If the file format is unsupported the ConversionException will be thrown.

        :param file_path: path of the file to convert
        :param parameters: parameters of converting, see :ref:`parameters_description` for more details
        :return: path of converted file if conversion was executed
        """
        pass

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
                    raise ConversionError(msg=error_message)

        except subprocess.TimeoutExpired:
            message = f"Conversion of the {filename} hadn't terminated after {self.timeout} seconds"
            self.logger.error(message)
            raise ConversionError(msg=message)
