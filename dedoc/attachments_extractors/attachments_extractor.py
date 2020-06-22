import os
from collections import namedtuple
from typing import List

from dedoc.attachments_extractors.concrete_attach_extractors.excel_attachments_extractor import \
    ExcelAttachmentsExtractor
from dedoc.extensions import recognized_mimes
from dedoc.utils import get_file_mime_type, save_data_to_unique_file


AttachedFile = namedtuple("AttachedFile", ["original_name", "tmp_name_file"])


class AttachmentsExtractor(object):

    def get_attachments(self, tmp_dir: str, filename: str) -> List[AttachedFile]:
        """
        Search attachment files inside current file
        :return: List[original_name_attachment, tmp_names_attachment files in the tmp_dir]
        """
        mime = get_file_mime_type(os.path.join(tmp_dir, filename))
        attachment_binary_data = []

        if mime in recognized_mimes.excel_like_format:
            attachment_binary_data = ExcelAttachmentsExtractor().get_attachments(tmp_dir, filename)

        attachment_files = [AttachedFile(original_name, save_data_to_unique_file(tmp_dir, original_name, binary_data))
                            for original_name, binary_data in attachment_binary_data]

        return attachment_files
