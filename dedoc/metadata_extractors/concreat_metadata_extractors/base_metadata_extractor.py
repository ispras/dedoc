import os
from typing import Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concreat_metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor
from dedoc.utils.utils import get_file_mime_type


class BaseMetadataExtractor(AbstractMetadataExtractor):
    """
    Base class for metadata extractor. Inheritor should implement two methods: can_extract and add_metadata
    """

    def can_extract(self,
                    doc: UnstructuredDocument,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        check if this extractor can handle given file. Return True if can handle and False otherwise

        :type doc: document content
        :type directory: path to directory where original file and converted file are located
        :type filename: name of file after rename (for example 23141.doc)
        :type converted_filename: name of file after rename and conversion (for example 23141.docx)
        :type original_filename: file name before rename
        :type parameters: additional parameters
        :type other_fields: other fields
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
        add metadata to doc. Use this method only if this extractor can_extract this file

        :type document: document content
        :type directory: path to directory where original file and converted file are located
        :type filename: name of file after rename (for example 23141.doc)
        :type converted_filename: name of file after rename and conversion (for example 23141.docx)
        :type original_filename: file name before rename
        :type parameters: additional parameters
        :type other_fields: other fields
        """
        if parameters is None:
            parameters = {}
        meta_info = self._get_base_meta_information(directory, filename, original_filename, parameters)
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
