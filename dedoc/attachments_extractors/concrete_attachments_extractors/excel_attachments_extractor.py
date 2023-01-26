from typing import List

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import \
    AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.utils import splitext_


class ExcelAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extracts attachments from excel files
    """

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        attachments = []
        name, ext = splitext_(filename)
        if ext.lower() != '.xlsx':
            return attachments

        return self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="xl")
