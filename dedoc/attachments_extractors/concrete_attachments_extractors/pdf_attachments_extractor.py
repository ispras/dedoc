import logging
import os
import uuid
from typing import List, Tuple, Optional

import PyPDF2
from PyPDF2.pdf import PageObject
from PyPDF2.utils import PdfReadError

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.utils.utils import convert_datetime
from dedoc.attachments_extractors.utils import create_note


class PDFAttachmentsExtractor(AbstractAttachmentsExtractor):
    """
    Extract attachments from pdf files.
    """
    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the extractor, e.g. logger for logging
        """
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if this extractor can get attachments from the document (it should have .pdf extension)
        """
        return extension.lower() in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Get attachments from the given pdf document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        with open(os.path.join(tmpdir, filename), 'rb') as handler:
            try:
                reader = PyPDF2.PdfFileReader(handler)
            except Exception as e:
                self.logger.warning(f"can't handle {filename}, get {e}")
                return []
            attachments = []
            try:
                attachments.extend(self.__get_root_attachments(reader))
            except PdfReadError:
                self.logger.warning(f"{filename} is broken")
            try:
                attachments.extend(self.__get_page_level_attachments(reader))
            except PdfReadError:
                self.logger.warning(f"{filename} is broken")

        need_content_analysis = str(parameters.get("need_content_analysis", "false")).lower() == "true"
        return self._content2attach_file(content=attachments, tmpdir=tmpdir, need_content_analysis=need_content_analysis)

    def __get_notes(self, page: PageObject) -> List[Tuple[str, bytes]]:
        attachments = []
        if '/Annots' in page.keys():
            for annot in page['/Annots']:
                # Other subtypes, such as /Link, cause errors
                subtype = annot.getObject().get('/Subtype')
                if subtype == "/FileAttachment":
                    name = annot.getObject()['/FS']['/UF']
                    data = annot.getObject()['/FS']['/EF']['/F'].getData()  # The file containing the stream data.
                    attachments.append([name, data])
                if subtype == "/Text" and annot.getObject().get('/Name') == '/Comment':  # it is messages (notes) in PDF
                    note = annot.getObject()
                    created_time = convert_datetime(note["/CreationDate"]) if "/CreationDate" in note else None
                    modified_time = convert_datetime(note["/M"]) if "/M" in note else None
                    user = note.get("/T")
                    data = note.get("/Contents", "")

                    name, content = create_note(content=data,
                                                modified_time=modified_time,
                                                created_time=created_time,
                                                author=user)
                    attachments.append((name, bytes(content)))
        return attachments

    def __get_page_level_attachments(self, reader: PyPDF2.PdfFileReader) -> List[Tuple[str, bytes]]:
        cnt_page = reader.getNumPages()
        attachments = []
        for i in range(cnt_page):
            page = reader.getPage(i)
            attachments_on_page = self.__get_notes(page)
            attachments.extend(attachments_on_page)

        return attachments

    def __get_root_attachments(self, reader: PyPDF2.PdfFileReader) -> List[Tuple[str, bytes]]:
        """
        Retrieves the file attachments of the PDF as a dictionary of file names and the file data as a bytestring.

        :return: dictionary of filenames and bytestrings
        """
        attachments = []
        catalog = reader.trailer["/Root"]
        if '/Names' in catalog.keys() and '/EmbeddedFiles' in catalog['/Names'].keys() and '/Names' in catalog['/Names']['/EmbeddedFiles'].keys():
            file_names = catalog['/Names']['/EmbeddedFiles']['/Names']
            for f in file_names:
                if isinstance(f, str):
                    data_index = file_names.index(f) + 1
                    dict_object = file_names[data_index].getObject()
                    if '/EF' in dict_object and '/F' in dict_object['/EF']:
                        data = dict_object['/EF']['/F'].getData()
                        name = dict_object.get('/UF', "pdf_attach_{}".format(uuid.uuid1()))
                        attachments.append((name, data))

        return attachments
