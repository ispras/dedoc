from typing import List, Optional, Tuple

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader


class MhtmlReader(BaseReader):
    """
    This reader can process files with the following extensions: .mhtml, .mht, .mhtml.gz, .mht.gz
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        from dedoc.readers.html_reader.html_reader import HtmlReader

        super().__init__(config=config, recognized_extensions=recognized_extensions.mhtml_like_format, recognized_mimes=recognized_mimes.mhtml_like_format)
        self.html_reader = HtmlReader(config=self.config)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        from dedoc.utils.utils import get_mime_extension

        mime, extension = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        # this code differs from BaseReader because .eml and .mhtml files have the same mime type
        if extension:
            return extension.lower() in self._recognized_extensions
        return mime in self._recognized_mimes

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        from dedoc.utils.parameter_utils import get_param_attachments_dir, get_param_need_content_analysis, get_param_with_attachments

        parameters = {} if parameters is None else parameters
        attachments_dir = get_param_attachments_dir(parameters, file_path)

        names_list, original_names_list = self.__extract_files(path=file_path, save_dir=attachments_dir)
        names_html = self.__find_html(names_list=names_list)

        lines = []
        tables = []
        for html_file in names_html:
            result = self.html_reader.read(file_path=html_file, parameters=parameters)
            lines.extend(result.lines)
            tables.extend(result.tables)

        tmp_file_names = []
        original_file_names = []
        for tmp_file_name, original_file_name in zip(names_list, original_names_list):
            if tmp_file_name not in names_html:
                tmp_file_names.append(tmp_file_name)
                original_file_names.append(original_file_name)

        with_attachments = get_param_with_attachments(parameters)
        need_content_analysis = get_param_need_content_analysis(parameters)
        if with_attachments:
            attachments = self.__get_attachments(
                save_dir=attachments_dir, tmp_names_list=tmp_file_names, original_names_list=original_file_names, need_content_analysis=need_content_analysis
            )
        else:
            attachments = []

        return UnstructuredDocument(tables=tables, lines=lines, attachments=attachments)

    def __extract_files(self, path: str, save_dir: str) -> Tuple[List[str], List[str]]:
        import email
        import gzip
        import os
        from urllib.parse import urlparse
        from dedoc.utils.utils import check_filename_length, save_data_to_unique_file

        names_list = []
        original_names_list = []
        if path.endswith(".gz"):
            with gzip.open(path, "rt") as f:
                message = email.message_from_file(f)
        else:
            with open(path, "r") as f:
                message = email.message_from_file(f)
        self.logger.info(f"Extracting {path}")

        for part in message.walk():
            if part.is_multipart():
                continue
            content_type = part.get("Content-type", "")
            content_location = part["Content-Location"]
            content_name = os.path.basename(urlparse(content_location).path) or f"{os.path.basename(os.path.splitext(path)[0])}.html"
            if content_type == "text/html" and not content_name.endswith(".html"):
                content_name += ".html"

            content_name = check_filename_length(content_name)
            new_content_name = save_data_to_unique_file(directory=save_dir, filename=content_name, binary_data=part.get_payload(decode=True))

            names_list.append(os.path.join(save_dir, new_content_name))
            original_names_list.append(content_name)
        return names_list, original_names_list

    def __find_html(self, names_list: List[str]) -> List[str]:
        from bs4 import BeautifulSoup
        from dedoc.utils import supported_image_types
        from dedoc.utils.utils import get_encoding

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

    def __get_attachments(self, save_dir: str, tmp_names_list: List[str], original_names_list: List[str], need_content_analysis: bool) -> List[AttachedFile]:
        import os
        import uuid
        from dedoc.utils import supported_image_types

        attachments = []
        for tmp_file_name, original_file_name in zip(tmp_names_list, original_names_list):
            *_, extension = tmp_file_name.rsplit(".", maxsplit=1)
            if extension not in supported_image_types:
                continue
            attachment = AttachedFile(original_name=os.path.basename(original_file_name),
                                      tmp_file_path=os.path.join(save_dir, tmp_file_name),
                                      uid=f"attach_{uuid.uuid4()}",
                                      need_content_analysis=need_content_analysis)
            attachments.append(attachment)
        return attachments
