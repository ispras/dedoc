from abc import ABC, abstractmethod
from typing import List

from dedoc.data_structures.attached_file import AttachedFile


class BaseAttachmentsExtractor(ABC):
    """
    BaseAttachmentsExtractor is responsible for extracting attached files from PDF or docx file types
    """

    @abstractmethod
    def can_extract(self, mime: str, filename: str) -> bool:
        """
        Check if this Extractor can handle given file.
        :param mime: mime type of the file.
        :param filename: name of the file with extension. You can be sure that the file name consists only of letters
        numbers and dots.
        :return: True if this extractor can handle given file, False otherwise
        """
        pass

    @abstractmethod
    def get_attachments(self, tmpdir: str, filename: str) -> List[AttachedFile]:
        """
        Extract attachments from given file and save it in the tmpdir directory where the file is located
        This method can only be called on appropriate files,
        ensure that `can_extract` is True for given file.
        :param tmpdir: directory where file is located, all attached files should also be saved in this directory.
        :param filename: Name of the file from which you should extract attachments (not abs path, only file name, use
        os.path.join(tmpdir, filename) to obtain path)
        You can be sure that the file name consists only of letters
        numbers and dots.
        :return: list of AttachedFile (name of original file and abs path to the saved attachment file)
        """
        pass
