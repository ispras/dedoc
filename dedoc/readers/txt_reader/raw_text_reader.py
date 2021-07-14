import codecs
import re
from typing import Optional, Tuple, Iterable, List

from unicodedata import normalize
from bs4 import UnicodeDammit

from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.utils import calculate_file_hash


class RawTextReader(BaseReader):

    def __init__(self):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()
        self.space_regexp = re.compile(r"^\s+")

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
        encoding = self.__get_encoding(path=path, parameters=parameters)
        lines = self._get_lines_with_meta(path=path, encoding=encoding)
        lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
        encoding_warning = "encoding is {}".format(encoding)
        result = UnstructuredDocument(lines=lines, tables=[], attachments=[], warnings=[encoding_warning])
        return self._postprocess(result)

    def __get_encoding(self, path: str, parameters: dict) -> str:
        if "encoding" in parameters:
            return parameters["encoding"]
        else:
            with open(path, "rb") as file:
                blob = file.read()
                dammit = UnicodeDammit(blob)
                return dammit.original_encoding

    def _get_lines_with_meta(self, path: str, encoding: str) -> List[LineWithMeta]:
        lines = []
        file_hash = calculate_file_hash(path=path)
        number_of_empty_lines = 0
        for line_id, line in self._get_lines(path=path, encoding=encoding):
            metadata = ParagraphMetadata(page_id=0,
                                         line_id=line_id,
                                         predicted_classes=None,
                                         paragraph_type="raw_text")
            uid = "txt_{}_{}".format(file_hash, line_id)
            spacing_annotation_value = str(int(100 * (0.5 if number_of_empty_lines == 0 else number_of_empty_lines)))
            spacing_annotation = SpacingAnnotation(start=0, end=len(line), value=spacing_annotation_value)
            line_with_meta = LineWithMeta(line=line,
                                          hierarchy_level=None,
                                          metadata=metadata,
                                          annotations=[spacing_annotation],
                                          uid=uid)
            lines.append(line_with_meta)
            if line.isspace():
                number_of_empty_lines += 1
            else:
                number_of_empty_lines = 0

        return lines

    def _get_lines(self, path: str, encoding: str) -> Iterable[Tuple[int, str]]:
        with codecs.open(path, errors="ignore", encoding=encoding) as file:
            for line_id, line in enumerate(file):
                line = normalize('NFC', line).replace("й", "й")  # й replace matter
                yield line_id, line

    def __get_starting_spacing(self, line: Optional[LineWithMeta]) -> int:
        if line is None or line.line.isspace():
            return 0
        space_this = self.space_regexp.match(line.line.replace("\t", " " * 4))
        if space_this is None:
            return 0
        return space_this.end() - space_this.start()

    def __is_paragraph(self, line: LineWithMeta, previous_line: Optional[LineWithMeta]) -> bool:
        space_this = self.__get_starting_spacing(line)
        space_prev = self.__get_starting_spacing(previous_line)
        return (line.hierarchy_level.is_raw_text() and
                not line.line.isspace() and
                space_this - space_prev >= 2)

    def _postprocess(self, document: UnstructuredDocument) -> UnstructuredDocument:
        previous_line = None
        for line in document.lines:
            is_paragraph = self.__is_paragraph(line=line, previous_line=previous_line)
            line.hierarchy_level.can_be_multiline = not is_paragraph
            previous_line = line
        return document
