from typing import List, Optional

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.utils.utils import splitext_


class ExcelAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extracts attachments from xlsx files.
    """
    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if this extractor can get attachments from the document (it should have .xlsx extension)
        """
        return extension.lower() in recognized_extensions.excel_like_format or mime in recognized_mimes.excel_like_format

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Get attachments from the given xlsx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        attachments = []
        name, ext = splitext_(filename)
        if ext.lower() != '.xlsx':
            return attachments

        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="xl")
