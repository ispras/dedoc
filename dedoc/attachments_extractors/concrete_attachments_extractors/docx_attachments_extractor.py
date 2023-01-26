import hashlib
import os
import tempfile
import zipfile
from typing import List

from bs4 import BeautifulSoup

from dedoc.attachments_extractors.concrete_attachments_extractors.abstract_office_attachments_extractor import \
    AbstractOfficeAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.utils import splitext_


class DocxAttachmentsExtractor(AbstractOfficeAttachmentsExtractor):
    """
    Extract attachments from docx files
    """

    def __extract_diagrams(self, document: zipfile.ZipFile) -> List[tuple]:
        """
        creates files for diagram: for each paragraph with diagram one file
        :returns: list files with diagrams
        """
        result = []
        bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
        paragraphs = [p for p in bs.body]
        diagram_paragraphs = []
        for paragraph in paragraphs:
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

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        :param tmpdir: directory where file is located
        :param filename: Name of the file from which you should extract attachments
        :param parameters: dict with different parameters for extracting
        :return: list of lists (name of original file and binary file content)
        """
        result = []
        name, ext = splitext_(filename)

        if ext.lower() != '.docx':
            return []

        with zipfile.ZipFile(os.path.join(tmpdir, filename), 'r') as zfile:
            diagram_attachments = self.__extract_diagrams(zfile)
            result += self._content2attach_file(content=diagram_attachments, tmpdir=tmpdir, need_content_analysis=False)

        result += self._get_attachments(tmpdir=tmpdir, filename=filename, parameters=parameters, attachments_dir="word")
        return result
