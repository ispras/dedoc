from typing import List, Optional
from zipfile import BadZipFile, ZipFile

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.attached_file import AttachedFile


class DocxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from docx files.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        super().__init__(config=config, recognized_extensions=recognized_extensions.docx_like_format, recognized_mimes=recognized_mimes.docx_like_format)

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given docx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        import os
        from dedoc.utils.parameter_utils import get_param_need_content_analysis

        parameters = {} if parameters is None else parameters
        tmpdir, filename = os.path.split(file_path)
        result = []
        try:
            with ZipFile(os.path.join(tmpdir, filename), "r") as zfile:
                diagram_attachments = self.__extract_diagrams(zfile)
                need_content_analysis = get_param_need_content_analysis(parameters)
                result += self._content2attach_file(content=diagram_attachments, tmpdir=tmpdir, need_content_analysis=need_content_analysis,
                                                    parameters=parameters)

            result += self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="word")

        except BadZipFile:
            raise BadFileFormatError(f"Bad docx file:\n file_name = {filename}. Seems docx is broken")
        return result

    def __extract_diagrams(self, document: ZipFile) -> List[tuple]:
        """
        Creates files for diagram: separate file for each paragraph with diagram.

        :param document: archive with docx document
        :returns: list of files with diagrams
        """
        import hashlib
        import os
        import re
        import tempfile
        from bs4 import BeautifulSoup, Tag

        result = []
        try:
            content = document.read("word/document.xml")
        except KeyError:
            content = document.read("word/document2.xml")

        content = re.sub(br"\n[\t ]*", b"", content)
        bs = BeautifulSoup(content, "xml")

        paragraphs = [p for p in bs.body]
        diagram_paragraphs = []
        for paragraph in paragraphs:
            if not isinstance(paragraph, Tag):
                continue

            extracted = paragraph.extract()
            if extracted.pict:
                diagram_paragraphs.append(extracted)
        if not diagram_paragraphs:
            return result

        with tempfile.TemporaryDirectory() as tmpdir:
            document.extractall(tmpdir)
            namelist = document.namelist()

            for p in diagram_paragraphs:
                bs.body.insert(1, p)
                doc_text = str(bs)
                paragraph = p.extract()
                uid = hashlib.md5(paragraph.encode()).hexdigest()

                with open(f"{tmpdir}/word/document.xml", "w") as f:
                    f.write(doc_text)
                diagram_name = f"{uid}.docx"
                with ZipFile(os.path.join(tmpdir, diagram_name), mode="w") as new_d:
                    for filename in namelist:
                        new_d.write(os.path.join(tmpdir, filename), arcname=filename)
                with open(os.path.join(tmpdir, diagram_name), "rb") as f:
                    result.append((diagram_name, f.read()))
        return result
