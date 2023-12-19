from typing import Dict, Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor


class StructureExtractorComposition(AbstractStructureExtractor):
    """
    This class allows to extract structure from any document according to the available list of structure extractors.
    The list of structure extractors and names of document types for them is set via the class constructor.
    Each document type defines some specific document domain, those structure is extracted via the corresponding structure extractor.
    """
    def __init__(self, extractors: Dict[str, AbstractStructureExtractor], default_key: str, *, config: Optional[dict] = None) -> None:
        """
        :param extractors: mapping document_type -> structure extractor, defined for certain document domains
        :param default_key: the document_type of the structure extractor, that will be used by default if the wrong parameters are given. \
        default_key should exist as a key in the extractors' dictionary.
        """
        super().__init__(config=config)
        assert default_key in extractors
        self.extractors = extractors
        self.default_extractor_key = default_key

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Adds information about the document structure according to the document type received from parameters (the key `document_type`).
        If there isn't `document_type` key in parameters or this document_type isn't found in the supported types, the default extractor will be used.
        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """
        parameters = {} if parameters is None else parameters
        document_type = parameters.get("document_type", self.default_extractor_key)
        extractor = self.extractors.get(document_type, self.extractors[self.default_extractor_key])
        return extractor.extract(document, parameters)
