from abc import ABC, abstractmethod
from typing import List, Union


class BaseConcreteAttachmentsExtractor(ABC):
    """
    BaseConcreteAttachmentsExtractor is responsible for extracting attached files from PDF or docx file types
    """

    @abstractmethod
    def can_extract(self, mime: str, filename: str) -> bool:
        """
        Checks if this Extractor can handle given file.
        :param mime: mime type of the file.
        :param filename: name of the file with extension. You can be sure that the file name consists only of letters
        numbers and dots.
        :return: True if this extractor can handle given file, False otherwise
        """
        pass

    @abstractmethod
    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[List[Union[str, bytes]]]:
        """
        Extracts attachments from given file and return name of attachment and containing in bytes.
        This method can only be called on appropriate files,
        ensure that `can_extract` is True for given file.
        :param tmpdir: directory where file is located
        :param filename: Name of the file from which you should extract attachments (not abs path, only file name, use
        os.path.join(tmpdir, filename) to obtain path)
        :param parameters: dict with different parameters for extracting
        You can be sure that the file name consists only of letters
        numbers and dots.
        :return: List[[attacment_name, attachment_byte]] - list of attachment name file and
                containing of attachment file in bytes
        """
        pass
