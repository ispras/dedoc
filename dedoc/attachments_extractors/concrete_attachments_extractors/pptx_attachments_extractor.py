from typing import List

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import \
    AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.utils import splitext_


class PptxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from docx files
    """

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        result = []
        name, ext = splitext_(filename)

        if ext.lower() != ".pptx":
            return result

        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="ppt")
