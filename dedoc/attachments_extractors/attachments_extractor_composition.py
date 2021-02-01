import inspect
import logging
import os
from typing import List

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_attachment_extractor import \
    AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils import get_file_mime_type, save_data_to_unique_file


class AttachmentsExtractorComposition:

    def __init__(self, extractors: List[AbstractAttachmentsExtractor], *, config: dict):
        self.extractors = extractors
        self.config = config
        self.logger = self.config.get("logger", logging.getLogger())

    def get_attachments(self, tmp_dir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Search attachment files inside current file
        :return: List[original_name_attachment, tmp_names_attachment files in the tmp_dir]
        """
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))

        for extractor in self.extractors:
            if "parameters" in inspect.getfullargspec(extractor.can_extract).args:
                can_extract = extractor.can_extract(mime=mime, filename=filename, parameters=parameters)
            else:
                self.logger.warning("!WARNING! you extractor requires an update\n" +
                                    "Please specify parameters argument in method can_convert in {}\n".format(
                                        type(extractor).__name__) +
                                    " This parameters would be mandatory in the near future")
                can_extract = extractor.can_extract(mime=mime, filename=filename)
            if can_extract:
                attachment_binary_data = extractor.get_attachments(tmp_dir, filename, parameters)
                self.logger.debug("Save attachments in {}".format(tmp_dir))
                attachment_files = [
                    AttachedFile(original_name, save_data_to_unique_file(tmp_dir, original_name, binary_data))
                    for original_name, binary_data in attachment_binary_data
                ]
                return attachment_files
        return []
