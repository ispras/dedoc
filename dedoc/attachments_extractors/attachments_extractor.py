import os
from typing import List

from dedoc.attachments_extractors.base_attachments_extractor import BaseAttachmentsExtractor
from dedoc.attachments_extractors.base_concrete_attach_extractor import BaseConcreteAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils import get_file_mime_type, save_data_to_unique_file


class AttachmentsExtractor(BaseAttachmentsExtractor):

    def __init__(self, extractors: List[BaseConcreteAttachmentsExtractor]):
        super().__init__(extractors)

    def get_attachments(self, tmp_dir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Search attachment files inside current file
        :return: List[original_name_attachment, tmp_names_attachment files in the tmp_dir]
        """
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))

        for extractor in self.extractors:
            if extractor.can_extract(mime=mime, filename=filename):
                attachment_binary_data = extractor.get_attachments(tmp_dir, filename, parameters)
                attachment_files = [
                    AttachedFile(original_name, save_data_to_unique_file(tmp_dir, original_name, binary_data))
                    for original_name, binary_data in attachment_binary_data
                ]
                return attachment_files
        return []
