from typing import List, Optional
from collections import OrderedDict

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.serializable import Serializable


class ParsedDocument(Serializable):

    def __init__(self,
                 metadata: DocumentMetadata,
                 content: Optional[DocumentContent],
                 attachments: Optional[List["ParsedDocument"]] = None):
        """
        That class hold information about the document content, metadata and attachments.
        :param metadata: document metadata such as size, creation , creation date and so on
        :param content: text and tables
        :param attachments: result of analysis of attached files
        """
        self.metadata = metadata
        self.content = content
        self.attachments = attachments

    def add_attachments(self, new_attachment: List["ParsedDocument"]):
        if self.attachments is None:
            self.attachments = []
        self.attachments.extend(new_attachment)

    def set_metadata(self, metadata: DocumentMetadata):
        self.metadata = metadata

    def to_dict(self):
        res = OrderedDict()
        res["content"] = self.content.to_dict() if self.content is not None else []
        res["metadata"] = self.metadata.to_dict()
        if self.attachments is not None:
            res["attachments"] = [attachment.to_dict() for attachment in self.attachments]
        return res

