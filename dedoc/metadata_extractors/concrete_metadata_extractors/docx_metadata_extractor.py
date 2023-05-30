import os
from datetime import datetime
from typing import Optional

import docx
from docx.opc.exceptions import PackageNotFoundError

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class DocxMetadataExtractor(BaseMetadataExtractor):
    """
    This class is used to extract metadata from docx documents.
    It expands metadata retrieved by :class:`~dedoc.metadata_extractors.BaseMetadataExtractor`.

    In addition to them, the following fields can be added to the metadata other fields:
        - document subject;
        - keywords;
        - category;
        - comments;
        - author;
        - author who last modified the file;
        - created, modified and last printed date.
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
        Check if the document has .docx extension.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.add_metadata` documentation to get the information about parameters.
        """
        return converted_filename.lower().endswith("docx")

    def add_metadata(self,
                     document: UnstructuredDocument,
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: dict = None,
                     other_fields: Optional[dict] = None) -> UnstructuredDocument:
        """
        Add the predefined list of metadata for the docx documents.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.add_metadata` documentation to get the information about parameters.
        """
        if parameters is None:
            parameters = {}
        file_path = os.path.join(directory, converted_filename)
        docx_other_fields = self._get_docx_fields(file_path)
        if other_fields is not None and len(other_fields) > 0:
            docx_other_fields = {**docx_other_fields, **other_fields}

        meta_info = self._get_base_meta_information(directory, filename, original_filename, parameters)
        meta_info["other_fields"] = docx_other_fields
        document.metadata = meta_info
        return document

    def __convert_date(self, date: Optional[datetime]) -> Optional[int]:
        if date is not None:
            return int(date.timestamp())
        return None

    def _get_docx_fields(self, file_path: str) -> dict:
        assert os.path.isfile(file_path)
        try:
            doc = docx.Document(file_path)
            properties = doc.core_properties
            parameters = {
                "document_subject": properties.subject,
                "keywords": properties.keywords,
                "category": properties.category,
                "comments": properties.comments,
                "author": properties.author,
                "last_modified_by": properties.last_modified_by,
                "created_date": self.__convert_date(properties.created),
                "modified_date": self.__convert_date(properties.modified),
                "last_printed_date": self.__convert_date(properties.last_printed),
            }
            return parameters
        except PackageNotFoundError:
            return {"broken_docx": True}
