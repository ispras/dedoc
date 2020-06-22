from typing import List, Optional
from collections import OrderedDict

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata


class ParsedDocument:

    def __init__(self,
                 metadata: DocumentMetadata,
                 content: DocumentContent,
                 attachments: Optional[List["ParsedDocument"]] = None):
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
        res["content"] = self.content.to_dict()
        res["metadata"] = self.metadata.to_dict()
        if self.attachments is not None:
            res["attachments"] = [attachment.to_dict() for attachment in self.attachments]
        return res

