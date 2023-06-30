import hashlib
import os
import re
import tempfile
import zipfile
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import AbstractOfficeAttachmentsExtractor
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes


class DocxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from docx files.
    """
    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if this extractor can get attachments from the document (it should have .docx extension)
        """
        return extension.lower() in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Get attachments from the given docx document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        result = []
        try:
            with zipfile.ZipFile(os.path.join(tmpdir, filename), 'r') as zfile:
                diagram_attachments = self.__extract_diagrams(zfile)
                need_content_analysis = str(parameters.get("need_content_analysis", "false")).lower() == "true"
                result += self._content2attach_file(content=diagram_attachments, tmpdir=tmpdir, need_content_analysis=need_content_analysis)

            result += self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="word")

        except zipfile.BadZipFile:
            raise BadFileFormatException("Bad docx file:\n file_name = {}. Seems docx is broken".format(filename))
        return result

    def __extract_diagrams(self, document: zipfile.ZipFile) -> List[tuple]:
        """
        Creates files for diagram: separate file for each paragraph with diagram.

        :param document: archive with docx document
        :returns: list of files with diagrams
        """
        result = []
        try:
            content = document.read('word/document.xml')
        except KeyError:
            content = document.read('word/document2.xml')

        content = re.sub(br"\n[\t ]*", b"", content)
        bs = BeautifulSoup(content, 'xml')

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

                with open(f'{tmpdir}/word/document.xml', 'w') as f:
                    f.write(doc_text)
                diagram_name = f"{uid}.docx"
                with zipfile.ZipFile(os.path.join(tmpdir, diagram_name), mode='w') as new_d:
                    for filename in namelist:
                        new_d.write(os.path.join(tmpdir, filename), arcname=filename)
                with open(os.path.join(tmpdir, diagram_name), "rb") as f:
                    result.append((diagram_name, f.read()))
        return result
