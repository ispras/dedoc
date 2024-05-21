import os
from datetime import datetime
from typing import Optional

import docx
from docx.opc.exceptions import PackageNotFoundError

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class DocxMetadataExtractor(AbstractMetadataExtractor):
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

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.docx_like_format, recognized_mimes=recognized_mimes.docx_like_format)
        self.base_extractor = BaseMetadataExtractor(config=config)

    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None) -> dict:
        """
        Add the predefined list of metadata for the docx documents.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract` documentation to get the information about parameters.
        """
        parameters = {} if parameters is None else parameters
        file_dir, file_name, converted_filename, original_filename = self._get_names(file_path, converted_filename, original_filename)

        base_fields = self.base_extractor.extract(
            file_path=file_path, converted_filename=converted_filename, original_filename=original_filename, parameters=parameters
        )
        docx_fields = self._get_docx_fields(os.path.join(file_dir, converted_filename))

        result = {**base_fields, **docx_fields}
        return result

    def __convert_date(self, date: Optional[datetime]) -> Optional[int]:
        return None if date is None else int(date.timestamp())

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
