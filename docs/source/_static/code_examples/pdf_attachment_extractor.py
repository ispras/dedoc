import os
from typing import List, Optional

import PyPDF2

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes


class PdfAttachmentsExtractor(AbstractAttachmentsExtractor):
    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return extension in recognized_extensions.pdf_like_format or mime in recognized_mimes.pdf_like_format

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        handler = open(os.path.join(tmpdir, filename), "rb")
        reader = PyPDF2.PdfFileReader(handler)
        catalog = reader.trailer["/Root"]
        attachments = []
        if "/Names" not in catalog or "/EmbeddedFiles" not in catalog["/Names"]:
            return attachments
        filenames = catalog["/Names"]["/EmbeddedFiles"]["/Names"]
        for filename in filenames:
            if isinstance(filename, str):
                name = filename
                data_index = filenames.index(filename) + 1
                f_dict = filenames[data_index].getObject()
                f_data = f_dict["/EF"]["/F"].getData()
                attachments.append((name, f_data))
        attachments = self._content2attach_file(content=attachments, tmpdir=tmpdir, need_content_analysis=False, parameters=parameters)
        return attachments
