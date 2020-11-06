from typing import List, Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.metadata_extractor.concreat_metadata_extractors.abstract_metadata_extractor import AbstractMetadataExtractor


class MetadataExtractorComposition:

    def __init__(self, extractors: List[AbstractMetadataExtractor]):
        """
        Use list of extractors to extract metadata from file. Use first appropriate extractor (one that can_extract is
        True). Thus order of extractors is important
        """
        self.extractors = extractors

    def add_metadata(self,
                     doc: Optional[DocumentContent],
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     parameters: dict = None) -> ParsedDocument:
        for extractor in self.extractors:
            if extractor.can_extract(doc=doc,
                                     directory=directory,
                                     filename=filename,
                                     converted_filename=converted_filename,
                                     original_filename=original_filename,
                                     parameters=parameters):
                return extractor.add_metadata(doc=doc,
                                              directory=directory,
                                              filename=filename,
                                              converted_filename=converted_filename,
                                              original_filename=original_filename,
                                              parameters=parameters)
        raise Exception("Can't extract metadata from from file {}".format(filename))
