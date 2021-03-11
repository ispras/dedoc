import logging
from typing import List

from dedoc.attachment_extractors.abstract_attachment_extractor import \
    AbstractAttachmentsExtractor
from dedoc.data_structures.unstructured_document import UnstructuredDocument


class AttachmentsHandler:

    def __init__(self, extractors: List[AbstractAttachmentsExtractor], *, config: dict):
        self.extractors = extractors
        self.config = config
        self.logger = self.config.get("logger", logging.getLogger())

    def handle_attachments(self, document: UnstructuredDocument, parameters: dict):
        """
        Handle attached files, for example save it on disk or S3 storage
        """
        pass
