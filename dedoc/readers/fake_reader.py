from typing import Optional, Tuple

from dedoc.readers.base_reader import BaseReader
from dedoc.data_structures.line_with_meta import LineWithMeta, ParagraphMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


class FakeReader(BaseReader):
    def read(self,
             path: str,
             document_type: Optional[str],
             parameters: Optional[dict]) -> Tuple[UnstructuredDocument, bool]:

        with open(path) as f:
            readed_lines = f.read().splitlines()

        lines = []

        for i, line in enumerate(readed_lines):
            metadata = ParagraphMetadata(HierarchyLevel.raw_text, None, 0, None)
            level = HierarchyLevel(1, 0, False, HierarchyLevel.raw_text)
            lines.append(LineWithMeta(line, level, metadata, []))

        return UnstructuredDocument(lines=lines, tables=[]), False

    def can_read(self, path: str, mime: str, extension: str, document_type: str) -> bool:
        return (extension in [".html", ".shtml"] or mime in ["text/html"]) and not document_type
