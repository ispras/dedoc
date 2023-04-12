from typing import List, Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concrete_metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor


class MetadataExtractorComposition:

    def __init__(self, extractors: List[AbstractMetadataExtractor]) -> None:
        """
        Use list of extractors to extract metadata from file. Use first appropriate extractor (one that can_extract is
        True). Thus order of extractors is important
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
        raise Exception("Can't extract metadata from from file {}".format(filename))
