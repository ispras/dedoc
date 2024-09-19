from typing import List, Optional

from dedoc.api.schema.parsed_document import ParsedDocument as ApiParsedDocument
from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.serializable import Serializable


class ParsedDocument(Serializable):
    """
    This class holds information about the document content, metadata and attachments.

    :ivar content: document text (hierarchy of nodes) and tables
    :ivar attachments: result of analysis of attached files (empty if with_attachments=False)
    :ivar metadata: document metadata such as size, creation date and so on.
    :ivar warnings: list of warnings and possible errors, arising in the process of document parsing

    :vartype content: DocumentContent
    :vartype attachments: List[ParsedDocument]
    :vartype metadata: DocumentMetadata
    :vartype warnings: List[str]
    """
    def __init__(self,
                 metadata: DocumentMetadata,
                 content: DocumentContent,
                 warnings: Optional[List[str]] = None,
                 attachments: Optional[List["ParsedDocument"]] = None) -> None:
        """
        :param metadata: document metadata such as size, creation date and so on.
        :param content: text and tables
        :param attachments: result of analysis of attached files
        :param warnings: list of warnings and possible errors, arising in the process of document parsing
        """
        self.metadata: DocumentMetadata = metadata
        self.content: DocumentContent = content
        self.attachments: List["ParsedDocument"] = [] if attachments is None else attachments
        self.warnings: List[str] = warnings if warnings is not None else []

    def add_attachments(self, new_attachment: List["ParsedDocument"]) -> None:
        if self.attachments is None:
            self.attachments = []
        self.attachments.extend(new_attachment)

    def set_metadata(self, metadata: DocumentMetadata) -> None:
        self.metadata = metadata

    def to_api_schema(self) -> ApiParsedDocument:
        import dedoc.version

        content = self.content.to_api_schema()
        metadata = self.metadata.to_api_schema()
        attachments = [attachment.to_api_schema() for attachment in self.attachments] if self.attachments is not None else []
        return ApiParsedDocument(content=content, metadata=metadata, version=dedoc.version.__version__, warnings=self.warnings, attachments=attachments)
