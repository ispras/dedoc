from abc import ABC, abstractmethod
from typing import Optional, Tuple

from dedoc.data_structures.unstructured_document import UnstructuredDocument


class BaseReader(ABC):

    @abstractmethod
    def read(self,
             path: str,
             document_type: Optional[str],
             parameters: Optional[dict]) -> Tuple[UnstructuredDocument, bool]:
        """
        read file from disc and extract text from it. File should have appropriate extension and type

        :param path: path to the file in file system
        :param document_type: type of file, for example law, technical specification, scientific article and so on
        :param parameters: dicts with additional parameters for document reader (as language for scans or delimeter for
        csv reader)
        :return: Tuple: 1)  parsed document and 2) flag if file can contain attachments
        """
        pass

    @abstractmethod
    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: str,
                 parameters: Optional[dict] = None) -> bool:
        """
        check if this reader can handle given file. This method should work fast, so do not read whole file
        :param path:  path to the file in file system
        :param mime: MIME type of a file
        :param extension: file extension, for example .doc or .pdf
        :param document_type:  type of file, for example law, technical specification, scientific article and so on
        :param parameters: dicts with additional parameters for document reader (as language for scans or delimeter for
        csv reader)
        :return: True if this Reader can handle file, false otherwise
        """
        pass
