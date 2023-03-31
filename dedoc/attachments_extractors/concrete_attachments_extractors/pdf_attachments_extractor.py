import logging
import os
import uuid
from typing import List, Tuple

import PyPDF2
from PyPDF2.pdf import PageObject
from PyPDF2.utils import PdfReadError

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.utils import convert_datetime
from dedoc.attachments_extractors.utils import create_note


class PDFAttachmentsExtractor(AbstractAttachmentsExtractor):

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        with open(os.path.join(tmpdir, filename), 'rb') as handler:
            try:
                reader = PyPDF2.PdfFileReader(handler)
            except Exception as e:
                self.logger.warning("can't handle {}, get {}".format(filename, e))
                return []
            attachments = []
            try:
                attachments.extend(self.__get_root_attachments(reader))
            except PdfReadError:
                self.logger.warning("{} is broken".format(filename))
            try:
                attachments.extend(self.__get_page_level_attachments(reader))
            except PdfReadError:
                self.logger.warning("{} is broken".format(filename))

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
        Retrieves the file attachments of the PDF as a dictionary of file names
        and the file data as a bytestring.
        :return: dictionary of filenames and bytestrings
        """
        attachments = []
        catalog = reader.trailer["/Root"]
        if ('/Names' in catalog.keys() and
                '/EmbeddedFiles' in catalog['/Names'].keys() and
                '/Names' in catalog['/Names']['/EmbeddedFiles'].keys()):
            fileNames = catalog['/Names']['/EmbeddedFiles']['/Names']
            for f in fileNames:
                if isinstance(f, str):
                    data_index = fileNames.index(f) + 1
                    dict_object = fileNames[data_index].getObject()
                    if '/EF' in dict_object and '/F' in dict_object['/EF']:
                        data = dict_object['/EF']['/F'].getData()
                        name = dict_object.get('/UF', "pdf_attach_{}".format(uuid.uuid1()))
                        attachments.append((name, data))

        return attachments
