from typing import List, Optional

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.utils.utils import splitext_


class PptxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from pptx files.
    """
    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if this extractor can get attachments from the document (it should have .pptx extension)
        """
        return extension.lower() in recognized_extensions.pptx_like_format or mime in recognized_mimes.pptx_like_format

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Get attachments from the given pptx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        result = []
        name, ext = splitext_(filename)

        if ext.lower() != ".pptx":
            return result

        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="ppt")
