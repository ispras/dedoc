import os
from typing import List, Optional

import PyPDF2

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.utils.utils import get_mime_extension


class PdfAttachmentsExtractor(AbstractAttachmentsExtractor):
    def can_extract(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension in recognized_extensions.pdf_like_format or mime in recognized_mimes.pdf_like_format

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        parameters = {} if parameters is None else parameters
        handler = open(os.path.join(file_path), "rb")
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
        attachments = self._content2attach_file(content=attachments, tmpdir=os.path.dirname(file_path), need_content_analysis=False, parameters=parameters)
        return attachments
