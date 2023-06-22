import os
from base64 import b64encode
from typing import Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor
from dedoc.utils.utils import get_file_mime_type


class BaseMetadataExtractor(AbstractMetadataExtractor):
    """
    This metadata extractor allows to extract metadata from the documents of any format.

    It returns the following information about the given file:
        - file name;
        - file type (MIME);
        - file size in bytes;
        - time when the file was last accessed;
        - time when the file was created;
        - time when the file was last modified.
    """

    def can_extract(self,
                    document: UnstructuredDocument,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        This extractor can handle any file so the method always returns True.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.can_extract` documentation to get the information about parameters.
        """
        return True

    def add_metadata(self,
                     document: UnstructuredDocument,
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: Optional[dict] = None,
                     other_fields: Optional[dict] = None) -> UnstructuredDocument:
        """
        Gets the basic meta-information about the file.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.add_metadata` documentation to get the information about parameters.
        """
        parameters = {} if parameters is None else parameters
        meta_info = self._get_base_meta_information(directory, filename, original_filename, parameters)

        if parameters.get("is_attached", False) and str(parameters.get("return_base64", "false")).lower() == "true":
            other_fields = {} if other_fields is None else other_fields

            path = os.path.join(directory, filename)
            with open(path, "rb") as file:
                other_fields["base64_encode"] = b64encode(file.read()).decode("utf-8")

        if other_fields is not None and len(other_fields) > 0:
            meta_info["other_fields"] = other_fields
        document.metadata = meta_info
        return document

    @staticmethod
    def _get_base_meta_information(directory: str, filename: str, name_actual: str, parameters: dict) -> dict:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(os.path.join(directory, filename))
        meta = {
            "file_name": name_actual,
            "file_type": get_file_mime_type(os.path.join(directory, filename)),
            "size": size,  # in bytes
            "access_time": atime,
            "created_time": ctime,
            "modified_time": mtime
        }

        return meta
