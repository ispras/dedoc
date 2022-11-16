import re
from typing import Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor


class DefaultStructureExtractor(AbstractStructureExtractor):

    def __init__(self) -> None:
        self.chapter = re.compile(r"^(статья|пункт|параграф|глава|определение)\s*([0-9]+\.)*([0-9]+\.?)")  # noqa
        self.dotted_num = re.compile(r"^([0-9]+\.)+([0-9]+\.?)?(\s|$)")
        self.bracket_num = re.compile(r"^[0-9]+\)")
        self.letter = re.compile(r"^(([а-я]|[a-z])\))")

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        previous_header = None
        previous_hierarchy_level = None
        for line in document.lines:
            hierarchy_level = line.hierarchy_level

            if hierarchy_level is None or self.chapter.match(line.line.lower().strip()):
                hierarchy_level = self.__get_hierarchy_level_single_line(
                    line=line,
                    previous_header=previous_header,
                    previous_hierarchy_level=previous_hierarchy_level
                )
            if not hierarchy_level.is_raw_text():
                previous_header = line.line
                previous_hierarchy_level = hierarchy_level

            line.set_hierarchy_level(hierarchy_level)
            line.metadata.paragraph_type = hierarchy_level.paragraph_type
            assert line.hierarchy_level is not None

        return document

    def __get_hierarchy_level_single_line(self,
                                          line: LineWithMeta,
                                          previous_header: Optional[str],
                                          previous_hierarchy_level: Optional[Tuple[int, int]]) -> HierarchyLevel:

        line_text = line.line.lower().strip()
        if self.chapter.match(line_text):
            res = self._get_named(line_text)
            assert res is not None
            return res
        else:
            res = self._get_hierarchy_level_list(line, previous_header, previous_hierarchy_level)
            assert res is not None
            return res

    def __match_line_with_headers(self, line: LineWithMeta, headers: list) -> Tuple[str, int]:
        for index, header in enumerate(headers):
            h_s = header.split('\n')  # разбивка по строкам
            count_line_of_headers = len(h_s)
            first_string = h_s[0]  # поиск совпадения по первой строке предполагаемого заголовка
            first_string = first_string.lower().strip()
            if first_string == line:
                headers.pop(index)
                return header, count_line_of_headers - 1
        return "", 0

    def _get_named(self, line: str) -> HierarchyLevel:
        line = line.strip()
        if line.startswith("глава"):
            return HierarchyLevel(1, 1, False, paragraph_type="named_header")
        elif line.startswith("статья"):
            return HierarchyLevel(1, 2, False, paragraph_type="named_header")
        elif line.startswith("пункт"):
            return HierarchyLevel(1, 3, False, paragraph_type="named_header")
        elif line.startswith("параграф"):
            return HierarchyLevel(1, 4, False, paragraph_type="named_header")
        elif line.startswith("№"):
            return HierarchyLevel(1, 5, False, paragraph_type="named_header")
        return HierarchyLevel.create_raw_text()

    def _get_hierarchy_level_list(self,
                                  line: LineWithMeta,
                                  previous_header: Optional[str],
                                  previous_hierarchy_level: Optional[Tuple[int, int]]) -> HierarchyLevel:
        line_text = line.line.lower().strip()
        if self.dotted_num.match(line_text):
            line_num = [n for n in line_text.strip().split()[0].split(".") if len(n) > 0]
            if (
                    all((float(n) <= 1900 for n in line_num)) and  # FIX dates like 9.05.1945
                    len(line_text.split()[0]) <= 9  # too long items is rare a list
            ):
                return HierarchyLevel(2, len(line_num), False, paragraph_type=HierarchyLevel.list_item)
        elif self.bracket_num.match(line_text):
            line_num = [n for n in line_text.strip().split()[0].split(".") if len(n) > 0]
            first_item = line_text.split()[0]

            # now we check if tesseract recognize russian б as 6 (bi as six)
            if (
                    first_item == "6)" and
                    previous_header is not None and
                    previous_header.strip().startswith(("a)", "а)"))  # here is russian and english letters
            ):
                return HierarchyLevel(4, 1, False, paragraph_type=HierarchyLevel.list_item)
            return HierarchyLevel(3, len(line_num), False, paragraph_type=HierarchyLevel.list_item)
        elif self.letter.match(line_text):
            return HierarchyLevel(4, 1, False, paragraph_type=HierarchyLevel.list_item)
        return HierarchyLevel.create_raw_text()
