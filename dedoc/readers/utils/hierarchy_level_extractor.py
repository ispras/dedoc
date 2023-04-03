import re
from typing import Optional, List, Iterable

from dedoc.data_structures.line_with_meta import LineWithMeta, HierarchyLevel
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth


class HierarchyLevelExtractor:
    # TODO: move to other extractor
    chapter = re.compile("^(статья|пункт|параграф|глава|определение)\s*([0-9]+\\.)*([0-9]+\\.?)")  # noqa
    # TODO: There is in dedoc/structure_extractors/hierarchy_level_builders/utils_reg.py
    dotted_num = re.compile("^([0-9]+\\.)+([0-9]+\\.?)?(\\s|$)")
    dotted_without_space_num = re.compile(r"^\d+\.[a-z]")  # TODO: it's dirty hack for pmi, please remove
    # TODO: There is in dedoc/structure_extractors/hierarchy_level_builders/utils_reg.py
    bracket_num = re.compile("^[0-9]+\\)")
    letter = re.compile("^(([а-я]|[a-z])\\))")

    def __init__(self) -> None:
        self.in_block_header = False

    @staticmethod
    def need_update_level(hierarchy_level: HierarchyLevel, extracted_level: HierarchyLevel) -> bool:
        if hierarchy_level is None:
            return True

        return extracted_level.level_1 is not None

    def get_hierarchy_level(self, lines: Iterable[LineWithMeta]) -> List[LineWithMeta]:
        previous_line_text = None
        result = []
        for line in lines:
            hierarchy_level = line.hierarchy_level
            extracted_level = self.__get_hierarchy_level_single_line(line=line, previous_line_text=previous_line_text)

            if HierarchyLevelExtractor.need_update_level(hierarchy_level, extracted_level):
                hierarchy_level = extracted_level

            if not hierarchy_level.is_raw_text():
                previous_line_text = line.line

            line.set_hierarchy_level(hierarchy_level)
            assert line.hierarchy_level is not None
            result.append(line)

        return result

    def __get_hierarchy_level_single_line(self, line: LineWithMeta, previous_line_text: Optional[str]) -> HierarchyLevel:

        line_text = line.line.lower().strip()
        '''
        TODO: Move self.chapter.match into default structure extractor in case we don't have tags in a document
        P.S. Ломающее много тестов изменение. Нужно аккуратно перенести в default structure extractor
        '''
        if self.chapter.match(line_text):
            res = self._get_named(line_text)
            assert res is not None
            return res

        if line.metadata._tag.paragraph_type == "header":
            return self.get_default_tag_hl_header(line.metadata._tag.level_2 if line.metadata._tag.level_2
                                                  else self.get_dotted_depth_of_list(line_text))
        else:
            res = self.get_hierarchy_level_list(line, previous_line_text)
            assert res is not None
            return res

    def _get_named(self, line: str) -> HierarchyLevel:
        # TODO this code must be in other_structure_extractor
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

    @staticmethod
    def get_dotted_depth_of_list(line_text: str) -> Optional[int]:
        # TODO remove, similar code exists in dedoc/structure_extractors/feature_extractors/list_features/list_utils.py
        #  (only without dotted_without_space_num)
        if HierarchyLevelExtractor.dotted_num.match(line_text):
            line_num = [n for n in line_text.strip().split()[0].split(".") if len(n) > 0]
            if (all((float(n) <= 1900 for n in line_num)) and  # FIX dates like 9.05.1945
                    len(line_text.split()[0]) <= 9):  # too long items is rare a list
                return len(line_num)
        elif HierarchyLevelExtractor.dotted_without_space_num.match(line_text):
            line_num = [line_text.split(".")[0]]
            if all((float(n) <= 1900 for n in line_num)):  # FIX dates like 9.05.1945
                return len(line_num)

        return None

    @staticmethod
    def get_hierarchy_level_list(line: LineWithMeta, previous_line_text: Optional[str]) -> HierarchyLevel:
        line_text = line.line.lower().strip()

        dotted_depth = get_dotted_item_depth(line_text)
        if dotted_depth != -1:
            return HierarchyLevel(2, dotted_depth, False, paragraph_type=HierarchyLevel.list_item)

        elif HierarchyLevelExtractor.bracket_num.match(line_text):
            line_num = [n for n in line_text.strip().split()[0].split(".") if len(n) > 0]
            first_item = line_text.split()[0]

            # now we check if tesseract recognize russian б as 6 (bi as six)
            if (first_item == "6)" and
                    previous_line_text is not None and
                    previous_line_text.strip().startswith(("a)", "а)"))):  # here is russian and english letters

                return HierarchyLevel(4, 1, False, paragraph_type=HierarchyLevel.list_item)
            return HierarchyLevel(3, len(line_num), False, paragraph_type=HierarchyLevel.list_item)
        elif HierarchyLevelExtractor.letter.match(line_text):
            return HierarchyLevel(4, 1, False, paragraph_type=HierarchyLevel.list_item)
        return HierarchyLevel.create_raw_text()
