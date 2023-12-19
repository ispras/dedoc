import copy
import logging
import os
import time
from typing import List, Optional

from dedoc.attachments_extractors import AbstractAttachmentsExtractor
from dedoc.common.exceptions.dedoc_error import DedocError
from dedoc.data_structures import AttachedFile, DocumentMetadata, ParsedDocument
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.utils.utils import get_empty_content


class AttachmentsHandler:
    """
    This class is used for handling attached files:

        - they may be stored in the custom directory (use `attachments_dir` key in the parameters to set output directory path);
        - they may be ignored (if the option `with_attachments=false` in parameters);
        - the metadata of the attachments may be added without files parsing (if `with_attachments=true, need_content_analysis=false` in parameters)
        - they may be parsed (if `with_attachments=true, need_content_analysis=true` in parameters), \
            the parsing recursion may be set via `recursion_deep_attachments` parameter.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        """
        :param config: configuration of the handler, e.g. logger for logging
        """
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())

    def handle_attachments(self, document_parser: "DedocManager", document: UnstructuredDocument, parameters: dict) -> List[ParsedDocument]:  # noqa
        """
        Handle attachments of the document in the intermediate representation.

        :param document_parser: class with `parse` method for parsing attachments if needed;
        :param document: intermediate representation of the document whose attachments need to be handled;
        :param parameters: parameters for attachments handling (with_attachments, need_content_analysis, recursion_deep_attachments, attachments_dir \
            are important, look to the API parameters documentation for more details).
        :return: list of parsed document attachments
        """
        parsed_attachment_files = []
        recursion_deep_attachments = int(parameters.get("recursion_deep_attachments", 10)) - 1

        if not AbstractAttachmentsExtractor.with_attachments(parameters) or recursion_deep_attachments < 0:
            return parsed_attachment_files

        previous_log_time = time.time()

        for i, attachment in enumerate(document.attachments):
            current_time = time.time()
            if current_time - previous_log_time > 3:
                previous_log_time = current_time  # not log too often
                self.logger.info(f"Handle attachment {i} of {len(document.attachments)}")

            if not attachment.get_original_filename():  # TODO check for docx https://jira.ispras.ru/browse/TLDR-185
                continue

            parameters_copy = copy.deepcopy(parameters)
            parameters_copy["is_attached"] = True
            parameters_copy["recursion_deep_attachments"] = str(recursion_deep_attachments)

            try:
                if attachment.need_content_analysis:
                    parsed_file = document_parser.parse(attachment.get_filename_in_path(), parameters=parameters_copy)
                else:
                    parsed_file = self.__get_empty_document(document_parser=document_parser, attachment=attachment, parameters=parameters_copy)

                parsed_file.metadata.file_name = attachment.original_name  # initial name of the attachment
                parsed_file.metadata.temporary_file_name = os.path.split(attachment.get_filename_in_path())[-1]  # actual name in the file system
            except DedocError:
                # return empty ParsedDocument with Meta information
                parsed_file = self.__get_empty_document(document_parser=document_parser, attachment=attachment, parameters=parameters_copy)

            parsed_file.metadata.set_uid(attachment.uid)
            parsed_attachment_files.append(parsed_file)
        return parsed_attachment_files

    def __get_empty_document(self, document_parser: "DedocManager", attachment: AttachedFile, parameters: dict) -> ParsedDocument:  # noqa
        metadata = document_parser.document_metadata_extractor.extract(
            file_path=attachment.get_filename_in_path(),
            original_filename=attachment.get_original_filename(),
            parameters=parameters
        )
        metadata = DocumentMetadata(**metadata)
        return ParsedDocument(content=get_empty_content(), metadata=metadata)
