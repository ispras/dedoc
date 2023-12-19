import os
import zipfile
from abc import ABC
from typing import List, Optional, Tuple

import olefile
from charset_normalizer import from_bytes

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile


class AbstractOfficeAttachmentsExtractor(AbstractAttachmentsExtractor, ABC):
    """
    Extract attachments from files of Microsoft Office format like docx, pptx, xlsx.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def __parse_ole_contents(self, stream: bytes) -> Tuple[str, bytes]:
        """
        Parse the binary content of olefile.

        :param stream: binary content of olefile
        :return: tuple of (name of original file and binary file content)
        """
        # original filename in ANSI starts at byte 7 and is null terminated
        stream = stream[6:]

        last_name_pos = 0
        for ord_chr in stream:
            if ord_chr == 0:
                break
            last_name_pos += 1

        filename_binary = stream[:last_name_pos]
        dammit = from_bytes(filename_binary)
        filename = filename_binary.decode(encoding=dammit.best().encoding)

        stream = stream[len(filename) + 1:]
        filesize = 0
        # original filepath in ANSI is next and is null terminated
        for ord_chr in stream:
            if ord_chr == 0:
                break
            filesize += 1

        # next 4 bytes are unused
        stream = stream[filesize + 1 + 4:]
        # size of the temporary file path in ANSI in little endian
        temporary_filepath_size = 0
        temporary_filepath_size |= stream[0] << 0
        temporary_filepath_size |= stream[1] << 8
        temporary_filepath_size |= stream[2] << 16
        temporary_filepath_size |= stream[3] << 24
        stream = stream[4 + temporary_filepath_size:]
        size = 0  # size of the contents in little endian
        size |= stream[0] << 0
        size |= stream[1] << 8
        size |= stream[2] << 16
        size |= stream[3] << 24
        stream = stream[4:]
        contents = stream[:size]  # contents
        return filename, contents

    def _get_attachments(self, tmpdir: str, filename: str, parameters: dict, attachments_dir: str) -> List[AttachedFile]:
        result = []

        with zipfile.ZipFile(os.path.join(tmpdir, filename), "r") as zfile:
            files = zfile.namelist()
            attachments = [file for file in files if file.startswith((f"{attachments_dir}/media/", f"{attachments_dir}/embeddings/"))]

            for attachment in attachments:
                original_name = os.path.split(attachment)[-1]

                # these are windows metafile extensions
                if original_name.endswith((".emf", "wmf")):
                    continue

                if not original_name.endswith(".bin"):
                    result.append((original_name, zfile.read(attachment)))
                else:
                    with zfile.open(attachment) as f:
                        ole = olefile.OleFileIO(f.read())

                    # extracting PDF-files
                    if ole.exists("CONTENTS"):
                        data = ole.openstream("CONTENTS").read()
                        if data[0:5] == b"%PDF-":
                            result.append((f"{os.path.splitext(original_name)[-2]}.pdf", data))

                    # extracting files in other formats
                    elif ole.exists("\x01Ole10Native"):
                        original_name, contents = self.__parse_ole_contents(ole.openstream("\x01Ole10Native").read())
                        result.append((original_name, contents))

                    # TODO process any ole files except \x01Ole10Native and PDF (looks like impossible task)

            need_content_analysis = str(parameters.get("need_content_analysis", "false")).lower() == "true"
            attachments = self._content2attach_file(content=result, tmpdir=tmpdir, need_content_analysis=need_content_analysis, parameters=parameters)
            return attachments
