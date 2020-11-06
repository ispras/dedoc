import os
from datetime import datetime
from typing import Optional

import docx

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from metadata_extractor.concreat_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class DocxMetadataExtractor(BaseMetadataExtractor):

    def __init__(self) -> None:
        super().__init__()

    def can_extract(self,
                    doc: Optional[DocumentContent],
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: dict = None) -> bool:
        return converted_filename.endswith("docx")

    def add_metadata(self,
                     doc: Optional[DocumentContent],
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     parameters: dict = None) -> ParsedDocument:
        if parameters is None:
            parameters = {}
        file_path = os.path.join(directory, converted_filename)

        meta_info = self._get_base_meta_information(directory, filename, original_filename, parameters)
        metadata = DocumentMetadata(
            file_name=meta_info["file_name"],
            file_type=meta_info["file_type"],
            size=meta_info["size"],
            access_time=meta_info["access_time"],
            created_time=meta_info["created_time"],
            modified_time=meta_info["modified_time"],
            other_fields=self._get_docx_fields(file_path)
        )
        parsed_document = ParsedDocument(metadata=metadata, content=doc)
        return parsed_document

    def __convert_date(self, date: Optional[datetime]):
        if date is not None:
            return int(date.timestamp())
        return None

    def _get_docx_fields(self, file_path: str) -> dict:
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
