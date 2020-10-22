import codecs
from typing import Optional, Tuple, Iterable

from unicodedata import normalize

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.configuration_manager import get_manager_config
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor
from dedoc.data_structures.line_with_meta import LineWithMeta


class RawTextReader(BaseReader):

    def __init__(self):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()

    def _get_lines(self, path: str) -> Iterable[Tuple[int, str]]:
        with codecs.open(path, errors="ignore", encoding="utf-8-sig") as file:
            for line_id, line in enumerate(file):
                line = normalize('NFC', line).replace("й", "й")  # й replace matter
                yield line_id, line

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:
        lines = []
        for line_id, line in self._get_lines(path):
            metadata = get_manager_config()['paragraph_metadata']().full_fields(page_id=0,
                                                                              line_id=line_id,
                                                                              predicted_classes=None,
                                                                              paragraph_type="raw_text")
            line_with_meta = LineWithMeta(line=line, hierarchy_level=None, metadata=metadata, annotations=[])
            lines.append(line_with_meta)
        lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
        return UnstructuredDocument(lines=lines, tables=[]), False

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str]) -> bool:
        return extension.endswith(".txt") and not document_type
