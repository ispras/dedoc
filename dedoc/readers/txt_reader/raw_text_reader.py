from typing import Optional, Tuple

from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor
from dedoc.data_structures.line_with_meta import LineWithMeta


class RawTextReader(BaseReader):

    def __init__(self):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:
        with open(path) as file:
            lines = []
            for line_id, line in enumerate(file):
                metadata = ParagraphMetadata(page_id=0,
                                             line_id=line_id,
                                             predicted_classes=None,
                                             paragraph_type="raw_text")
                line_with_meta = LineWithMeta(line=line, hierarchy_level=None, metadata=metadata, annotations=[])
                lines.append(line_with_meta)
            lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
        return UnstructuredDocument(lines=lines, tables=[]), False

    def can_read(self, path: str, mime: str, extension: str, document_type: str) -> bool:
        return extension.endswith(".txt")


