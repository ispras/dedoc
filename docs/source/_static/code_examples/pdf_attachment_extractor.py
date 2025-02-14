import os
from typing import List, Optional

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.utils.parameter_utils import get_param_attachments_dir, get_param_need_content_analysis
from dedoc.utils.utils import get_mime_extension


class PdfAttachmentsExtractor(AbstractAttachmentsExtractor):
    def can_extract(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        mime, extension = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension in recognized_extensions.pdf_like_format or mime in recognized_mimes.pdf_like_format

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        from pypdf import PdfReader

        parameters = {} if parameters is None else parameters
        with open(os.path.join(file_path), "rb") as f:
            reader = PdfReader(f)
            catalog = reader.trailer["/Root"]

            if "/Names" not in catalog or "/EmbeddedFiles" not in catalog["/Names"]:
                return []

            attachments = []
            filenames = catalog["/Names"]["/EmbeddedFiles"]["/Names"]
            for filename in filenames:
                if isinstance(filename, str):
                    name = filename
                    data_index = filenames.index(filename) + 1
                    f_dict = filenames[data_index].get_object()
                    f_data = f_dict["/EF"]["/F"].get_data()
                    attachments.append((name, f_data))

        attachments_dir = get_param_attachments_dir(parameters, file_path)
        need_content_analysis = get_param_need_content_analysis(parameters)
        attachments = self._content2attach_file(content=attachments, tmpdir=attachments_dir, need_content_analysis=need_content_analysis, parameters=parameters)
        return attachments
