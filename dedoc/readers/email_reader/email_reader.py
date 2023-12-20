import email
import json
import mimetypes
import os
import re
import uuid
from email.header import decode_header
from email.message import Message
from tempfile import NamedTemporaryFile
from typing import List, Optional

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.html_reader.html_reader import HtmlReader
from dedoc.utils.utils import get_mime_extension, get_unique_name, save_data_to_unique_file


class EmailReader(BaseReader):
    """
    This class is used for parsing documents with .eml extension (e-mail messages saved into files).
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.html_reader = HtmlReader(config=self.config)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension or mime is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return file_path.lower().endswith(".eml") or mime == "message/rfc822"

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        It also saves some data from the message's header (fields "subject", "from", "to", "cc", "bcc", "date", "reply-to")
        to the attached json file with prefix `message_header_`.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        attachments_dir = parameters.get("attachments_dir", None)
        attachments_dir = os.path.dirname(file_path) if attachments_dir is None else attachments_dir

        with open(file_path, "rb") as f:
            msg = email.message_from_binary_file(f)
        tables, attachments = [], []

        all_header_fields = dict(msg.items())
        lines = self.__get_main_fields(msg)
        header_filename = "message_header_" + get_unique_name("message_header.json")

        # saving message header into separated file as an attachment
        header_file_path = os.path.join(attachments_dir, header_filename)
        with open(header_file_path, "w", encoding="utf-8") as f:
            json.dump(all_header_fields, f, ensure_ascii=False, indent=4)

        need_content_analysis = str(parameters.get("need_content_analysis", "false")).lower() == "true"
        attachments.append(AttachedFile(original_name=header_filename,
                                        tmp_file_path=header_file_path,
                                        uid=f"attach_{uuid.uuid1()}",
                                        need_content_analysis=need_content_analysis))

        html_found = False
        text_parts = []
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            text_parts.append(msg)
        if content_type == "text/html":
            self.__add_content_from_html(msg, lines, tables, parameters)
            html_found = True

        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                text_parts.append(part)
                continue

            if content_type == "text/html":
                self.__add_content_from_html(part, lines, tables, parameters)
                html_found = True
                continue

            if part.is_multipart():
                continue

            self.__add_attachment(part, attachments_dir, attachments, need_content_analysis)

        # text/plain has the same content as text/html
        if not html_found:
            for text_part in text_parts:
                try:
                    self.__add_text_content(text_part, lines)
                except Exception as e:
                    self.logger.info(f"Error while text reading: {e}")

        return UnstructuredDocument(lines=lines, tables=tables, attachments=attachments)

    def __add_attachment(self, message: Message, attachments_dir: str, attachments: list, need_content_analysis: bool) -> None:
        content_type = message.get_content_type()
        payload = message.get_payload(decode=True)

        if payload is None or content_type == "text/plain" or content_type == "text/html":
            return

        filename = message.get_filename()
        filename = "" if filename is None else self.__get_decoded(filename)
        filename, extension = os.path.splitext(filename)
        filename = self.__fix_filename(filename)
        filename = str(uuid.uuid4()) if filename == "" else filename

        fixed_extension = self.__fix_filename(extension)
        if extension == "" or fixed_extension != extension:
            extension = mimetypes.guess_extension(content_type)
        extension = ".txt" if extension == ".bat" else extension

        filename = f"{filename}{extension}"
        tmp_file_name = save_data_to_unique_file(directory=attachments_dir, filename=filename, binary_data=payload)
        attachments.append(AttachedFile(original_name=filename,
                                        tmp_file_path=os.path.join(attachments_dir, tmp_file_name),
                                        uid=f"attach_{uuid.uuid1()}",
                                        need_content_analysis=need_content_analysis))

    def __add_content_from_html(self, message: Message, lines: list, tables: list, parameters: dict) -> None:
        payload = message.get_payload(decode=True)
        if payload is None:
            return
        if "\\u" in payload.decode():
            payload = message.get_payload()
            file = NamedTemporaryFile(mode="w")
        else:
            file = NamedTemporaryFile(mode="wb")

        file.write(payload)
        file.flush()
        document = self.html_reader.read(file_path=file.name, parameters=parameters)
        part_messages = [line for line in document.lines if line.line is not None]
        for line in part_messages:
            line._line += "\n"
        lines.extend(part_messages)
        tables.extend(document.tables)
        file.close()

    def __add_text_content(self, message: Message, lines: list) -> None:
        payload = message.get_payload(decode=True)
        if payload is None:
            return
        payload = payload.decode()
        if "\\u" in payload:
            # in this case the message wasn't encoded
            payload = message.get_payload()
        list_of_texts = payload.split("\n")
        for text in list_of_texts:
            text += "\n"
            lines.append(LineWithMeta(line=text,
                                      metadata=LineMetadata(tag_hierarchy_level=HierarchyLevel.create_unknown(), page_id=0, line_id=0),
                                      annotations=[]))

    def __fix_filename(self, filename: str) -> str:
        filename = re.sub(r"[<>:\"/\\|?*]", "_", filename)
        filename = re.sub(r"\s+", " ", filename)
        return filename

    def __get_decoded(self, text: str) -> str:
        part = []
        for letter, encode in decode_header(text):
            if isinstance(letter, bytes):
                if encode is None:
                    encode = "ascii"
                letter = letter.decode(encoding=encode)
            part.append(letter)
        part = "".join(part)
        return part

    def __get_field(self, message: Message, key: str, line_metadata: LineMetadata) -> LineWithMeta:
        text = self.__get_decoded(message.get(key.lower(), ""))
        return LineWithMeta(line=text, metadata=line_metadata)

    def __get_main_fields(self, message: Message) -> List[LineWithMeta]:
        lines = list()
        line_metadata = LineMetadata(tag_hierarchy_level=HierarchyLevel(0, 0, False, "root"), page_id=0, line_id=0)
        lines.append(self.__get_field(message, "subject", line_metadata))

        required_fields = ["subject", "from", "to", "cc", "bcc", "date", "reply-to"]
        for field_name in required_fields:
            line_metadata = LineMetadata(tag_hierarchy_level=HierarchyLevel(1, 0, False, field_name), page_id=0, line_id=0)
            line = self.__get_field(message, field_name, line_metadata=line_metadata)
            if len(line.line) > 0:
                lines.append(line)

        return lines
