from typing import List, Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument
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
        :param extractors: the list of extractors with methods can_extract() and add_metadata() to extract metadata from file
        """
        self.extractors = extractors

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
        Add metadata to the document using one of the extractors if suitable extractor was found.
        Look to the method :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.add_metadata` of the class
        :class:`~dedoc.metadata_extractors.AbstractMetadataExtractor` documentation to get the information about method's parameters.
        """
        for extractor in self.extractors:
            if extractor.can_extract(document=document,
                                     directory=directory,
                                     filename=filename,
                                     converted_filename=converted_filename,
                                     original_filename=original_filename,
                                     parameters=parameters,
                                     other_fields=other_fields):
                return extractor.add_metadata(document=document,
                                              directory=directory,
                                              filename=filename,
                                              converted_filename=converted_filename,
                                              original_filename=original_filename,
                                              parameters=parameters,
                                              other_fields=other_fields,
                                              version=version)
        raise Exception(f"Can't extract metadata from from file {filename}")
