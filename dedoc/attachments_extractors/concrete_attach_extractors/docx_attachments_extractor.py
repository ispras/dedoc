import os
import zipfile
import olefile
from typing import List, Tuple, Union

from dedoc.attachments_extractors.base_concrete_attach_extractor import BaseConcreteAttachmentsExtractor
from dedoc.extensions import recognized_mimes
from dedoc.utils import splitext_


class DocxAttachmentsExtractor(BaseConcreteAttachmentsExtractor):
    """
    Extract attachments from docx files
    """

    @staticmethod
    def __parse_ole_contents(stream: bytes) -> Tuple[str, bytes]:
        """
        Parse the binary content of olefile
        :param stream: binary content of olefile
        :return: tuple of (name of original file and binary file content)
        """
        # original filename in ANSI starts at byte 7 and is null terminated
        stream = stream[6:]
        filename = ""
        for ord_chr in stream:
            if ord_chr == 0:
                break
            filename += chr(ord_chr)
        stream = stream[len(filename) + 1:]
        filesize = 0
        # original filepath in ANSI is next and is null terminated
        for ord_chr in stream:
            if ord_chr == 0:
                break
            filesize += 1
        # next 4 bytes is unused
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

    def can_extract(self, mime: str, filename: str) -> bool:
        """
        Check if this Extractor can handle given file.
        :param mime: mime type of the file.
        :param filename: name of the file with extension.
        :return: True if this extractor can handle given file, False otherwise
        """

        if mime in recognized_mimes.docx_like_format:
            name, ext = splitext_(filename)
            return ext == '.docx'
        return False

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[List[Union[str, bytes]]]:
        """
        :param tmpdir: directory where file is located
        :param filename: Name of the file from which you should extract attachments
        :param parameters: dict with different parameters for extracting
        :return: list of lists (name of original file and binary file content)
        """
        result = []
        name, ext = splitext_(filename)

        if ext == '.docx':
            with zipfile.ZipFile(os.path.join(tmpdir, filename), 'r') as zfile:
                files = zfile.namelist()

                attachments = [file for file in files if file.startswith("word/media/")]
                attachments += [file for file in files if file.startswith("word/embeddings/")]
                try:
                    for attachment in attachments:
                        namefile = os.path.split(attachment)[-1]
                        if not namefile.endswith('.emf') and not namefile.endswith('.bin'):
                            result.append([namefile, zfile.read(attachment)])

                        elif namefile.endswith('.bin'):
                            # extracting PDF-files
                            with zfile.open(attachment) as f:
                                ole = olefile.OleFileIO(f.read())
                            if ole.exists("CONTENTS"):
                                data = ole.openstream('CONTENTS').read()
                                if data[0:5] == b'%PDF-':
                                    result.append([os.path.splitext(namefile)[-1] + '.pdf', data])
                            # extracting files in other formats
                            elif ole.exists("\x01Ole10Native"):
                                data = ole.openstream("\x01Ole10Native").read()
                                namefile, contents = self.__parse_ole_contents(data)
                                result.append([namefile, contents])
                except Exception as error:
                    print(error)
        return result
