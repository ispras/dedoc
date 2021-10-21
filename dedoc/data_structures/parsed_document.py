from typing import List, Optional
from collections import OrderedDict

from flask_restx import fields, Api, Model

from dedoc.config import get_config
from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.serializable import Serializable


class ParsedDocument(Serializable):

    def __init__(self,
                 metadata: DocumentMetadata,
                 content: Optional[DocumentContent],
                 version: Optional[str] = None,
                 warnings: List[str] = None,
                 attachments: Optional[List["ParsedDocument"]] = None):
        """
        That class hold information about the document content, metadata and attachments.
        :param metadata: document metadata such as size, creation , creation date and so on
        :param content: text and tables
        :param attachments: result of analysis of attached files
        :param version: the version of the program that parsed this document
        :param warnings: list of warnings and possible errors, arising in the process of document parsing
        """
        self.metadata = metadata
        self.content = content
        self.attachments = [] if attachments is None else attachments
        self.version = version
        self.warnings = warnings if warnings is not None else []

    def add_attachments(self, new_attachment: List["ParsedDocument"]):
        if self.attachments is None:
            self.attachments = []
        self.attachments.extend(new_attachment)

    def set_metadata(self, metadata: DocumentMetadata):
        self.metadata = metadata

    def to_dict(self, old_version: bool):
        res = OrderedDict()
        res["version"] = self.version
        res["warnings"] = self.warnings
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
            'version': fields.String(description='the version of the program that parsed this document',
                                     example="2020.07.11"),
            'warnings': fields.List(fields.String(description='list of warnings and possible errors',
                                    example="DOCX: seems that document corrupted")),
            'attachments': fields.List(fields.Nested(api.model('others_ParsedDocument', {})),
                                       description='structure of attachments',
                                       required=False)
            if depth == get_config()['recursion_deep_attachments']
            else fields.List(fields.Nested(ParsedDocument.get_api_dict(api,
                                                                       depth=depth + 1,
                                                                       name='refParsedDocument' + str(depth)),
                                           description='Attachment structure',
                                           required=False))})
