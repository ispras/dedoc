import logging
import os
from typing import Optional

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.utils.utils import convert_datetime


class PdfMetadataExtractor(BaseMetadataExtractor):
    """
    This class is used to extract metadata from pdf documents.
    It expands metadata retrieved by :class:`~dedoc.metadata_extractors.BaseMetadataExtractor`.

    In addition to them, the following fields can be added to the metadata other fields:
        - producer;
        - creator;
        - author;
        - title;
        - subject;
        - keywords;
        - creation date;
        - modification date.
    """
    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the extractor, e.g. logger for logging
        """
        super().__init__()
        self.keys = {
            "/Producer": "producer",
            "/Creator": "creator",
            "/Author": "author",
            "/Title": "title",
            "/Subject": "subject",
            "/Keywords": "keywords"
        }

        self.keys_date = {
            "/CreationDate": "creation_date",
            "/ModDate": "modification_date",
        }
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def can_extract(self,
                    document: UnstructuredDocument,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: dict = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        Check if the document has .pdf extension.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.can_extract` documentation to get the information about parameters.
        """
        return filename.lower().endswith(".pdf")

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
        Add the predefined list of metadata for the pdf documents.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.add_metadata` documentation to get the information about parameters.
        """
        result = super().add_metadata(document=document,
                                      directory=directory,
                                      filename=filename,
                                      converted_filename=converted_filename,
                                      original_filename=original_filename,
                                      parameters=parameters,
                                      version=version,
                                      other_fields=other_fields)
        path = os.path.join(directory, filename)
        pdf_fields = self._get_pdf_info(path)
        if len(pdf_fields) > 0:
            result.metadata["other_fields"] = {**result.metadata.get("other_fields", {}), **pdf_fields}
        return result

    def _get_pdf_info(self, path: str) -> dict:
        try:
            with open(path, "rb") as file:
                document = PdfFileReader(file)
                document_info = document.getDocumentInfo() if document.getDocumentInfo() is not None else {}
                result = self.__prettify_metadata(document_info)
            return result
        except PdfReadError:
            return {"broken_pdf": True}
        except Exception as e:
            self.logger.warning("exception while extract pdf metadata: {} {}".format(path, e))
            if self.config.get("debug_mode", False):
                raise e
            return {"broken_pdf": True}

    def __prettify_metadata(self, document_info: dict) -> dict:
        result = {}
        for key, value in document_info.items():
            if isinstance(value, str) and len(value) > 0:
                if key in self.keys:
                    result[self.keys[key]] = value
                elif key in self.keys_date:
                    try:
                        date = convert_datetime(value)
                    except:  # noqa
                        date = None
                    if date is not None:
                        result[self.keys_date[key]] = date
        return result
