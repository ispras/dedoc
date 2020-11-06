from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.parsed_document import ParsedDocument


class AbstractMetadataExtractor(ABC):

    @abstractmethod
    def can_extract(self,
                    doc: Optional[DocumentContent],
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: dict = None) -> bool:
        pass

    @abstractmethod
    def add_metadata(self,
                     doc: Optional[DocumentContent],
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     parameters: dict = None) -> ParsedDocument:
        pass
