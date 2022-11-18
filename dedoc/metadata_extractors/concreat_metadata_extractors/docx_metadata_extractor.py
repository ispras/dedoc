import os
from datetime import datetime
from typing import Optional

import docx
from docx.opc.exceptions import PackageNotFoundError

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concreat_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class DocxMetadataExtractor(BaseMetadataExtractor):

    def __init__(self) -> None:
        super().__init__()

    def can_extract(self,
                    doc: UnstructuredDocument,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        return converted_filename.endswith("docx")

    def add_metadata(self,
                     document: UnstructuredDocument,
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: dict = None,
                     other_fields: Optional[dict] = None) -> UnstructuredDocument:
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
