import logging

from dedoc.data_structures.unstructured_document import UnstructuredDocument


class AttachmentsHandler:

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = self.config.get("logger", logging.getLogger())

    def handle_attachments(self, document: UnstructuredDocument, parameters: dict) -> None:
        """
        Handle attached files, for example save it on disk or S3 storage
        """
        pass
