from typing import IO, Iterator, List, Optional

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader


class ArchiveReader(BaseReader):
    """
    This reader allows to get archived files as attachments of the :class:`~dedoc.data_structures.UnstructuredDocument`.
    Documents with the following extensions can be parsed: .zip, .tar, .tar.gz, .rar, .7z.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        super().__init__(config=config, recognized_extensions=recognized_extensions.archive_like_format, recognized_mimes=recognized_mimes.archive_like_format)

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return empty content of archive, all content will be placed inside attachments.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        from dedoc.utils.parameter_utils import get_param_attachments_dir, get_param_need_content_analysis, get_param_with_attachments

        parameters = {} if parameters is None else parameters

        with_attachments = get_param_with_attachments(parameters)
        if not with_attachments:
            return UnstructuredDocument(lines=[], tables=[], attachments=[])

        attachments_dir = get_param_attachments_dir(parameters, file_path)
        need_content_analysis = get_param_need_content_analysis(parameters)
        attachments = self.__get_attachments(path=file_path, tmp_dir=attachments_dir, need_content_analysis=need_content_analysis)
        return UnstructuredDocument(lines=[], tables=[], attachments=attachments)

    def __get_attachments(self, path: str, tmp_dir: str, need_content_analysis: bool) -> List[AttachedFile]:
        import rarfile
        import tarfile
        import zipfile
        from dedoc.utils.utils import get_file_mime_type

        mime = get_file_mime_type(path)
        if zipfile.is_zipfile(path) and mime == "application/zip":
            return list(self.__read_zip_archive(path=path, tmp_dir=tmp_dir, need_content_analysis=need_content_analysis))
        if tarfile.is_tarfile(path):
            return list(self.__read_tar_archive(path=path, tmp_dir=tmp_dir, need_content_analysis=need_content_analysis))
        if rarfile.is_rarfile(path):
            return list(self.__read_rar_archive(path=path, tmp_dir=tmp_dir, need_content_analysis=need_content_analysis))
        if mime == "application/x-7z-compressed":
            return list(self.__read_7z_archive(path=path, tmp_dir=tmp_dir, need_content_analysis=need_content_analysis))
        # if no one can handle this archive raise exception
        raise BadFileFormatError(f"bad archive {path}")

    def __read_zip_archive(self, path: str, tmp_dir: str, need_content_analysis: bool) -> Iterator[AttachedFile]:
        import zipfile
        import zlib

        try:
            with zipfile.ZipFile(path, "r") as arch_file:
                names = [member.filename for member in arch_file.infolist() if member.file_size > 0]
                for name in names:
                    with arch_file.open(name) as file:
                        yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file, need_content_analysis=need_content_analysis)
        except (zipfile.BadZipFile, zlib.error) as e:
            self.logger.warning(f"Can't read file {path} ({e})")
            raise BadFileFormatError(f"Can't read file {path} ({e})")

    def __read_tar_archive(self, path: str, tmp_dir: str, need_content_analysis: bool) -> Iterator[AttachedFile]:
        import tarfile

        with tarfile.open(path, "r") as arch_file:
            names = [member.name for member in arch_file.getmembers() if member.isfile()]
            for name in names:
                file = arch_file.extractfile(name)
                yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file, need_content_analysis=need_content_analysis)
                file.close()

    def __read_rar_archive(self, path: str, tmp_dir: str, need_content_analysis: bool) -> Iterator[AttachedFile]:
        import rarfile

        with rarfile.RarFile(path, "r") as arch_file:
            names = [item.filename for item in arch_file.infolist() if item.compress_size > 0]
            for name in names:
                with arch_file.open(name) as file:
                    yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file, need_content_analysis=need_content_analysis)

    def __read_7z_archive(self, path: str, tmp_dir: str, need_content_analysis: bool) -> Iterator[AttachedFile]:
        import py7zlib

        with open(path, "rb") as content:
            arch_file = py7zlib.Archive7z(content)
            names = arch_file.getnames()
            for name in names:
                file = arch_file.getmember(name)
                yield self.__save_archive_file(tmp_dir=tmp_dir, file_name=name, file=file, need_content_analysis=need_content_analysis)

    def __save_archive_file(self, tmp_dir: str, file_name: str, file: IO[bytes], need_content_analysis: bool) -> AttachedFile:
        import os
        import uuid
        from dedoc.utils.utils import save_data_to_unique_file

        file_name = os.path.basename(file_name)
        binary_data = file.read()
        if isinstance(binary_data, str):
            binary_data = binary_data.encode()
        tmp_path = save_data_to_unique_file(directory=tmp_dir, filename=file_name, binary_data=binary_data)
        attachment = AttachedFile(
            original_name=file_name,
            tmp_file_path=os.path.join(tmp_dir, tmp_path),
            need_content_analysis=need_content_analysis,
            uid=f"attach_{uuid.uuid1()}"
        )
        return attachment
