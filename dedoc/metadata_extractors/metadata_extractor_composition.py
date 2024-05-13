import logging
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
    def __init__(self, extractors: List[AbstractMetadataExtractor], *, config: Optional[dict] = None) -> None:
        """
        :param extractors: the list of extractors with methods can_extract() and extract() to extract metadata from file
        :param config: configuration dictionary, e.g. logger for logging
        """
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())
        self.extractors = extractors

    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None) -> dict:
        """
        Extract metadata using one of the extractors if suitable extractor was found.
        Look to the method :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract` of the class
        :class:`~dedoc.metadata_extractors.AbstractMetadataExtractor` documentation to get the information about method's parameters.
        """
        for extractor in self.extractors:
            if extractor.can_extract(file_path=file_path, converted_filename=converted_filename, original_filename=original_filename, parameters=parameters):
                return extractor.extract(file_path=file_path, converted_filename=converted_filename, original_filename=original_filename, parameters=parameters)
        raise Exception(f"Can't extract metadata from from file {os.path.basename(file_path)}")
