import copy
import logging
import os
import shutil
import tempfile
import time
from typing import List

from dedoc.attachments_extractors import AbstractAttachmentsExtractor
from dedoc.common.exceptions.dedoc_exception import DedocException
from dedoc.data_structures import ParsedDocument, DocumentMetadata, AttachedFile
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.utils.utils import get_empty_content


class AttachmentsHandler:

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = self.config.get("logger", logging.getLogger())

    def handle_attachments(self, document_parser: "DedocManager", document: UnstructuredDocument, parameters: dict) -> List[ParsedDocument]:  # noqa
        parsed_attachment_files = []
        if not AbstractAttachmentsExtractor.with_attachments(parameters):
            return parsed_attachment_files

        self.__move_attachments(document, parameters)
        self._handle_attachments(document=document, parameters=parameters)

        previous_log_time = time.time()

        for i, attachment in enumerate(document.attachments):
            current_time = time.time()
            if current_time - previous_log_time > 3:
                previous_log_time = current_time  # not log too often
                self.logger.info(f"Handle attachment {i} of {len(document.attachments)}")

            parameters_copy = copy.deepcopy(parameters)
            parameters_copy["is_attached"] = True
            parameters_copy["attachment"] = attachment
            recursion_deep_attachments = int(parameters_copy.get("recursion_deep_attachments", 10)) - 1
            parameters_copy["recursion_deep_attachments"] = str(recursion_deep_attachments)

            try:
                # TODO test recursion (https://jira.ispras.ru/browse/TLDR-300)
                if attachment.need_content_analysis and recursion_deep_attachments >= 0:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        attachment_path = os.path.join(tmpdir, attachment.get_original_filename())
                        shutil.copy(attachment.get_filename_in_path(), attachment_path)
                        parsed_file = document_parser.parse(attachment_path, parameters=parameters_copy)
                else:
                    parsed_file = self.__get_empty_document(document_parser=document_parser, attachment=attachment, parameters=parameters_copy)
            except DedocException:
                # return empty ParsedDocument with Meta information
                parsed_file = self.__get_empty_document(document_parser=document_parser, attachment=attachment, parameters=parameters_copy)

            parsed_file.metadata.set_uid(attachment.uid)
            parsed_attachment_files.append(parsed_file)
        return parsed_attachment_files

    def __move_attachments(self, document: UnstructuredDocument, parameters: dict) -> None:
        attachments_dir = parameters.get("attachments_dir")
        if attachments_dir is None:
            return

        for attachment in document.attachments:
            new_path = os.path.join(attachments_dir, os.path.split(attachment.get_filename_in_path())[1])
            shutil.move(attachment.get_filename_in_path(), new_path)
            attachment.tmp_file_path = new_path

    def _handle_attachments(self, document: UnstructuredDocument, parameters: dict) -> None:
        """
        Handle attached files, for example save it on disk or S3 storage.
        This method can be redefined by other AttachmentHandler class.
        """
        pass

    def __get_empty_document(self, document_parser: "DedocManager", attachment: AttachedFile, parameters: dict) -> ParsedDocument:  # noqa
        unstructured_document = UnstructuredDocument(lines=[], tables=[], attachments=[])
        attachment_dir, attachment_name = os.path.split(attachment.get_filename_in_path())
        unstructured_document = document_parser.document_metadata_extractor.add_metadata(document=unstructured_document, directory=attachment_dir,
                                                                                         filename=attachment_name, converted_filename=attachment_name,
                                                                                         original_filename=attachment.get_original_filename(),
                                                                                         parameters=parameters)
        metadata = DocumentMetadata(**unstructured_document.metadata)
        return ParsedDocument(content=get_empty_content(), metadata=metadata)
