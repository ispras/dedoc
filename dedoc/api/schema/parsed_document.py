from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.document_content import DocumentContent
from dedoc.api.schema.document_metadata import DocumentMetadata


class ParsedDocument(BaseModel):
    """
    Holds information about the document content, metadata and attachments.
    """
    content: DocumentContent = Field(description="Document text and tables")
    metadata: DocumentMetadata = Field(description="Document metadata such as size, creation date and so on")
    version: str = Field(description="Version of the program that parsed this document", example="0.9.1")
    warnings: List[str] = Field(description="List of warnings and possible errors, arising in the process of document parsing")
    attachments: List["ParsedDocument"] = Field(description="Result of analysis of attached files - list of `ParsedDocument`")
