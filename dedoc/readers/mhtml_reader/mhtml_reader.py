import email
import gzip
import logging
import os
import shutil
import tempfile
import uuid
from typing import Optional, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.utils import supported_image_types
from dedoc.utils.utils import get_encoding, calculate_file_hash
from dedoc.utils.utils import check_filename_length
from dedoc.readers.html_reader.html_reader import HtmlReader


class MhtmlReader(BaseReader):
    """
    This reader can process files with the following extensions: .mhtml, .mht, .mhtml.gz, .mht.gz
    """
    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the reader, e.g. logger for logging
        """
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self.mhtml_extensions = [".mhtml", ".mht"]
        self.mhtml_extensions += [f"{extension}.gz" for extension in self.mhtml_extensions]
        self.mhtml_extensions = tuple(self.mhtml_extensions)
        self.html_reader = HtmlReader(config=config)

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return extension.lower().endswith(tuple(self.mhtml_extensions))

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        save_dir = os.path.dirname(path)
        names_list = self.__extract_files(path=path, save_dir=save_dir)
        names_html = self.__find_html(names_list=names_list)

        lines = []
        tables = []
        for html_file in names_html:
            result = self.html_reader.read(path=html_file, parameters=parameters, document_type=document_type)
            lines.extend(result.lines)
            tables.extend(result.tables)

        need_content_analysis = str(parameters.get("need_content_analysis", "false")).lower() == "true"
        attachments_names = [os.path.join(os.path.basename(os.path.dirname(file_name)), os.path.basename(file_name))
                             for file_name in names_list if file_name not in names_html]
        attachments = self.__get_attachments(save_dir=save_dir, names_list=attachments_names, need_content_analysis=need_content_analysis)

        return UnstructuredDocument(tables=tables, lines=lines, attachments=attachments)

    def __extract_files(self, path: str, save_dir: str) -> List[str]:
        names_list = []
        if path.endswith(".gz"):
            with gzip.open(path, "rt") as f:
                message = email.message_from_file(f)
        else:
            with open(path, 'r') as f:
                message = email.message_from_file(f)
        self.logger.info('Extracting {}'.format(path))

        for part in message.walk():
            if part.is_multipart():
                continue
            content_type = part.get("Content-type", "")
            content_location = part['Content-Location']
            content_name = os.path.basename(urlparse(content_location).path) or '{}.html'.format(os.path.basename(os.path.splitext(path)[0]))
            if content_type == "text/html" and not content_name.endswith(".html"):
                content_name += ".html"

            content_name = check_filename_length(content_name)
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = os.path.join(tmpdir, content_name)
                with open(tmp_path, 'wb') as fp:
                    fp.write(part.get_payload(decode=True))

                file_hash = calculate_file_hash(tmp_path)
                file_dir = os.path.join(save_dir, file_hash)
                os.makedirs(file_dir, exist_ok=True)
                shutil.move(tmp_path, os.path.join(file_dir, content_name))

            names_list.append(os.path.join(file_dir, content_name))
        return names_list

    def __find_html(self, names_list: List[str]) -> List[str]:
        html_list = []
        for file_name in names_list:
            extension = file_name.split(".")[-1]
            if extension in supported_image_types:  # skip image files
                continue
            encoding = get_encoding(path=file_name, default="utf-8")
            try:
                with open(file_name, "r", encoding=encoding) as f:
                    soup = BeautifulSoup(f.read(), "html.parser").find()

                if soup and soup.name == "html":
                    html_list.append(file_name)
            except UnicodeDecodeError as e:
                self.logger.error(e)
        return html_list

    def __get_attachments(self, save_dir: str, names_list: List[str], need_content_analysis: bool) -> List[AttachedFile]:
        attachments = []
        for file_name in names_list:
            *_, extension = file_name.rsplit(".", maxsplit=1)
            if extension not in supported_image_types:
                continue
            attachment = AttachedFile(original_name=os.path.basename(file_name),
                                      tmp_file_path=os.path.join(save_dir, file_name),
                                      uid="attach_{}".format(uuid.uuid1()),
                                      need_content_analysis=need_content_analysis)
            attachments.append(attachment)
        return attachments
