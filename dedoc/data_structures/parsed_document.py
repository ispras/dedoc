from typing import List, Optional

import dedoc
from dedoc.api.schema.parsed_document import ParsedDocument as ApiParsedDocument
from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.serializable import Serializable


class ParsedDocument(Serializable):
    """
    This class holds information about the document content, metadata and attachments.
    """
    def __init__(self,
                 metadata: DocumentMetadata,
                 content: Optional[DocumentContent],
                 warnings: List[str] = None,
                 attachments: Optional[List["ParsedDocument"]] = None) -> None:
        """
        :param metadata: document metadata such as size, creation date and so on.
        :param content: text and tables
        :param attachments: result of analysis of attached files
        :param warnings: list of warnings and possible errors, arising in the process of document parsing
        """
        self.metadata = metadata
        self.content = content
        self.attachments = [] if attachments is None else attachments
        self.warnings = warnings if warnings is not None else []

    def add_attachments(self, new_attachment: List["ParsedDocument"]) -> None:
        if self.attachments is None:
            self.attachments = []
        self.attachments.extend(new_attachment)

    def set_metadata(self, metadata: DocumentMetadata) -> None:
        self.metadata = metadata

    def to_api_schema(self) -> ApiParsedDocument:
        content = self.content.to_api_schema()
        metadata = self.metadata.to_api_schema()
        attachments = [attachment.to_api_schema() for attachment in self.attachments] if self.attachments is not None else []
        return ApiParsedDocument(content=content, metadata=metadata, version=dedoc.__version__, warnings=self.warnings, attachments=attachments)
