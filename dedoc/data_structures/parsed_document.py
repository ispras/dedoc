from typing import List, Optional
from collections import OrderedDict

from flask_restplus import fields, Api, Model

from dedoc.config import get_config
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

    def to_dict(self, old_version: bool):
        res = OrderedDict()
        res["content"] = self.content.to_dict(old_version) if self.content is not None else []
        res["metadata"] = self.metadata.to_dict(old_version)
        if self.attachments is not None:
            res["attachments"] = [attachment.to_dict(old_version) for attachment in self.attachments]
        return res

    @staticmethod
    def get_api_dict(api: Api, depth: int = 0, name: str = 'ParsedDocument') -> Model:
        return api.model(name, {
            'content': fields.Nested(DocumentContent.get_api_dict(api), description='Document content structure'),
            'metadata': fields.Nested(DocumentMetadata.get_api_dict(api),
                                      allow_null=False,
                                      skip_none=True,
                                      description='Document meta information'),
            'attachments': fields.List(fields.Nested(api.model('others_ParsedDocument', {})),
                                       description='structure of attachments',
                                       required=False)
            if depth == get_config()['recursion_deep_attachments']
            else fields.List(fields.Nested(ParsedDocument.get_api_dict(api,
                                                                       depth=depth + 1,
                                                                       name='refParsedDocument' + str(depth)),
                                           description='Attachment structure',
                                           required=False))})
