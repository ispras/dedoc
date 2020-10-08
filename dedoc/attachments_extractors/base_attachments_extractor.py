
from abc import ABC, abstractmethod
from typing import List

from dedoc.data_structures.attached_file import AttachedFile


class BaseAttachmentsExtractor(ABC):
    """
    is an abstract base class for attachments extractor from List[BaseConcreteAttachmentsExtractor]
    """

    @abstractmethod
    def get_attachments(self, tmp_dir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Extract attachments from given file.
        This method can only be called on appropriate files,

        :param tmpdir: directory where file is located, all attached files should also be saved in this directory.
        :param filename: Name of the file from which you should extract attachments (not abs path, only file name, use
        os.path.join(tmpdir, filename) to obtain path)
        :param parameters: dict with different parameters for extracting
        You can be sure that the file name consists only of letters
        numbers and dots.
        :return: list of AttachedFile (name of original file and abs path to the saved attachment file)
        Note: name of original file will put into result json as metainfo.
        You can put any information in a string to display in the result (for example absolute path in the cloud storage
        or only name of attachment file)
        """
        pass