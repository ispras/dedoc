import os
from typing import List, Optional

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes


class ExcelAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extracts attachments from xlsx files.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.excel_like_format, recognized_mimes=recognized_mimes.excel_like_format)

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given xlsx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        parameters = {} if parameters is None else parameters
        tmpdir, filename = os.path.split(file_path)
        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="xl")
