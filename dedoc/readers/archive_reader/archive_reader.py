import logging
import os
import shutil
import tarfile
import uuid
import zipfile
import zlib
from mimetypes import guess_type
from tempfile import TemporaryDirectory
from typing import List, Optional, IO, Iterator, Tuple
import cv2
import numpy as np
import py7zlib
import rarfile

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_file_mime_type, save_data_to_unique_file


class ArchiveReader(BaseReader):

    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str], parameters: Optional[dict] = None) -> bool:
        if parameters is None:
            parameters = {}

        if ((extension.lower() in recognized_extensions.archive_like_format or
             mime in recognized_mimes.archive_like_format)):
            if parameters.get("archive_as_single_file", "true").lower() == "false":
                return True
            return not self.does_archive_content_scanned_files(path)

        return False

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        function return empty content of zip, all content will inside attachments
        """
        attachments = self.__get_attachments(path=path)
        return UnstructuredDocument(lines=[], tables=[], attachments=attachments)

    def __get_attachments(self, path: str) -> List[AttachedFile]:
        tmp_dir = os.path.dirname(path)
        mime = get_file_mime_type(path)
        if zipfile.is_zipfile(path) and mime == 'application/zip':
            return list(self.__read_zip_archive(path=path, tmp_dir=tmp_dir))
        if tarfile.is_tarfile(path):
            return list(self.__read_tar_archive(path=path, tmp_dir=tmp_dir))
        if rarfile.is_rarfile(path):
            return list(self.__read_rar_archive(path=path, tmp_dir=tmp_dir))
        if mime == 'application/x-7z-compressed':
            return list(self.__read_7z_archive(path=path, tmp_dir=tmp_dir))
        # if no one can handle this archive raise exception
        raise BadFileFormatException("bad archive {}".format(path))

    def __read_zip_archive(self, path: str, tmp_dir: str) -> Iterator[AttachedFile]:
        try:
            with zipfile.ZipFile(path, 'r') as arch_file:
                names = [member.filename for member in arch_file.infolist() if member.file_size > 0]
                for name in names:
                    with arch_file.open(name) as file:
                        yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file)
        except (zipfile.BadZipFile, zlib.error) as e:
            self.logger.warning("Can't read file {} ({})".format(path, e))
            raise BadFileFormatException("Can't read file {} ({})".format(path, e))

    def __read_tar_archive(self, path: str, tmp_dir: str) -> Iterator[AttachedFile]:
        with tarfile.open(path, 'r') as arch_file:
            names = [member.name for member in arch_file.getmembers() if member.isfile()]
            for name in names:
                file = arch_file.extractfile(name)
                yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file)
                file.close()

    def __read_rar_archive(self, path: str, tmp_dir: str) -> Iterator[AttachedFile]:
        with rarfile.RarFile(path, 'r') as arch_file:
            names = [item.filename for item in arch_file.infolist() if item.compress_size > 0]
            for name in names:
                with arch_file.open(name) as file:
                    yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file)

    def __read_7z_archive(self, path: str, tmp_dir: str) -> Iterator[AttachedFile]:
        with open(path, "rb") as content:
            arch_file = py7zlib.Archive7z(content)
            names = arch_file.getnames()
            for name in names:
                file = arch_file.getmember(name)
                yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file)

    def __save_archive_file(self, tmp_dir: str, file_name: str, file: IO[bytes]) -> AttachedFile:
        file_name = os.path.basename(file_name)
        binary_data = file.read()
        if isinstance(binary_data, str):
            binary_data = binary_data.encode()
        tmp_path = save_data_to_unique_file(directory=tmp_dir, filename=file_name, binary_data=binary_data)
        attachment = AttachedFile(
            original_name=file_name,
            tmp_file_path=os.path.join(tmp_dir, tmp_path),
            need_content_analysis=True,
            uid="attach_{}".format(uuid.uuid1())
        )
        return attachment

    def does_archive_content_scanned_files(self, path: str) -> bool:
        with TemporaryDirectory() as tmp_dir:
            path_out = os.path.join(tmp_dir, os.path.basename(path))
            shutil.copy(path, path_out)
            parsed_arch = self.__get_attachments(path_out)
            files = [file.original_name for file in parsed_arch]
            return self.__analyze_on_include_scans(files=files)

    def __is_hidden(self, file: str) -> bool:
        return file.split('/')[-1].startswith('.')

    def __analyze_on_include_scans(self, files: List[str]) -> bool:

        hidden_files = [file for file in files if self.__is_hidden(file)]

        path_order = [file for file in files if file.endswith('/order.csv') or file == 'order.csv']

        images = [file for file in files if guess_type(file)[0] in recognized_mimes.image_like_format and
                  file not in hidden_files]

        if len(path_order) > 0:
            files.remove(path_order[0])

        if len(files) - len(hidden_files) == len(images):
            return True
        else:
            return False

    def parse_archive_on_images(self, path: str) -> Tuple[int, Iterator[np.ndarray]]:
        attachments = self.__get_attachments(path)
        files = [file for file in attachments
                 if not file.tmp_file_path.endswith(".csv") and not self.__is_hidden(file.original_name)]
        order_csv = [file.tmp_file_path for file in attachments if file.tmp_file_path.endswith(".csv")]
        if len(order_csv) > 0:
            with open(order_csv[0]) as file:
                order_dict = {name: int(order) for name, order in map(lambda t: t.split(","), file)}
        else:
            order_dict = {}
        files.sort(key=lambda f: order_dict.get(f.original_name, f.original_name))

        return len(attachments), (cv2.imread(file.tmp_file_path) for file in files)
