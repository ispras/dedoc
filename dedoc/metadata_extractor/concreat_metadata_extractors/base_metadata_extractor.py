import os
from typing import Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.metadata_extractor.concreat_metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor
from dedoc.utils.utils import get_file_mime_type


class BaseMetadataExtractor(AbstractMetadataExtractor):
    """
    Base class for metadata extractor. Inheritor should implement two methods: can_extract and add_metadata
    """

    def can_extract(self,
                    doc: Optional[DocumentContent],
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
                     doc: Optional[DocumentContent],
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: Optional[dict] = None,
                     other_fields: Optional[dict] = None) -> ParsedDocument:
        """
        add metadata to doc. Use this method only if this extractor can_extract this file

        :type doc: document content
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
        metadata = DocumentMetadata(
            file_name=meta_info["file_name"],
            file_type=meta_info["file_type"],
            size=meta_info["size"],
            access_time=meta_info["access_time"],
            created_time=meta_info["created_time"],
            modified_time=meta_info["modified_time"]
        )
        if other_fields is not None and len(other_fields) > 0:
            metadata.extend_other_fields(other_fields)
        parsed_document = ParsedDocument(metadata=metadata, content=doc, version=version)
        return parsed_document

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
