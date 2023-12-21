import os
from typing import List, Optional

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.utils.utils import get_mime_extension, splitext_


class PptxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from pptx files.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def can_extract(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        """
        Checks if this extractor can get attachments from the document (it should have .pptx extension)
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in recognized_extensions.pptx_like_format or mime in recognized_mimes.pptx_like_format

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given pptx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        parameters = {} if parameters is None else parameters
        tmpdir, filename = os.path.split(file_path)
        result = []
        name, ext = splitext_(filename)

        if ext.lower() != ".pptx":
            return result

        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="ppt")
