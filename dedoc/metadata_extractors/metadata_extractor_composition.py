import os.path
from typing import List, Optional

from dedoc.metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor


class MetadataExtractorComposition:
    """
    This class allows to extract metadata from any document according to the available list of metadata extractors.
    The list of metadata extractors is set via the class constructor.
    The first suitable extractor is used (the one whose method :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.can_extract` \
    returns True), so the order of extractors is important.
    """
    def __init__(self, extractors: List[AbstractMetadataExtractor]) -> None:
        """
        :param extractors: the list of extractors with methods can_extract() and extract() to extract metadata from file
        """
        self.extractors = extractors

    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None,
                extension: Optional[str] = None,
                mime: Optional[str] = None) -> dict:
        """
        Extract metadata using one of the extractors if suitable extractor was found.

        :param file_path: path to the file to extract metadata. \
        If dedoc manager is used, the file gets a new name during processing - this name should be passed here (for example 23141.doc)
        :param converted_filename: name of the file after renaming and conversion (if dedoc manager is used, for example 23141.docx), \
        by default it's a name from the file_path. Converted file should be located in the same directory as the file before converting.
        :param original_filename: name of the file before renaming (if dedoc manager is used), by default it's a name from the file_path
        :param parameters: additional parameters for document parsing, see :ref:`parameters_description` for more details
        :param extension: file extension, for example .doc or .pdf
        :param mime: MIME type of file
        :return: dict with metadata information about the document
        """
        for extractor in self.extractors:
            if extractor.can_extract(
                file_path=file_path,
                converted_filename=converted_filename,
                original_filename=original_filename,
                parameters=parameters,
                extension=extension,
                mime=mime
            ):
                return extractor.extract(file_path=file_path, converted_filename=converted_filename, original_filename=original_filename, parameters=parameters)
        raise Exception(f"Can't extract metadata from from file {os.path.basename(file_path)}")
