import os
from typing import List, Optional

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes


class PptxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from pptx files.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.pptx_like_format, recognized_mimes=recognized_mimes.pptx_like_format)

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given pptx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        parameters = {} if parameters is None else parameters
        tmpdir, filename = os.path.split(file_path)
        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="ppt")
