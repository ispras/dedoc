import codecs
from typing import Optional, Tuple, Iterable, List

from unicodedata import normalize

from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.utils import calculate_file_hash


class RawTextReader(BaseReader):

    def __init__(self):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: Optional[str],
                 parameters: Optional[dict] = None) -> bool:
        return extension.endswith(".txt") and not document_type

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> UnstructuredDocument:
        lines = self._get_lines_with_meta(path)
        lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
        result = UnstructuredDocument(lines=lines, tables=[], attachments=[])
        return self._postprocess(result)

    def _get_lines_with_meta(self, path: str) -> List[LineWithMeta]:
        lines = []
        file_hash = calculate_file_hash(path=path)
        for line_id, line in self._get_lines(path):
            metadata = ParagraphMetadata(page_id=0,
                                         line_id=line_id,
                                         predicted_classes=None,
                                         paragraph_type="raw_text")
            uid = "txt_{}_{}".format(file_hash, line_id)
            line_with_meta = LineWithMeta(line=line, hierarchy_level=None, metadata=metadata, annotations=[], uid=uid)
            lines.append(line_with_meta)
        return lines

    def _get_lines(self, path: str) -> Iterable[Tuple[int, str]]:
        with codecs.open(path, errors="ignore", encoding="utf-8-sig") as file:
            for line_id, line in enumerate(file):
                line = normalize('NFC', line).replace("й", "й")  # й replace matter
                yield line_id, line

    def __is_paragraph(self, line: LineWithMeta) -> bool:
        return line.hierarchy_level.is_raw_text() and (line.line.isspace() or not line.line.startswith((" " * 2, "\t")))

    def _postprocess(self, document: UnstructuredDocument) -> UnstructuredDocument:
        for line in document.lines:
            if not self.__is_paragraph(line):
                line.hierarchy_level.can_be_multiline = False
        return document
