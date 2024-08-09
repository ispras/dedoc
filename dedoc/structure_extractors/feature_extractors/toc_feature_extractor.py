import re
from typing import List, Optional, Tuple

import numpy as np
from Levenshtein._levenshtein import ratio

from dedoc.data_structures.line_with_meta import LineWithMeta


class TocItem:
    """
    TocItem contains LineWithLabel and page.
    For example, line: 'Method implementation.....................45' converts to TocItem(line='Method implementation', page=45)
    """
    def __init__(self, line: LineWithMeta, page: int) -> None:
        self.line = line
        self.page = page

    def filter_toc_line(self, toc_item: "TocItem") -> "TocItem":
        # - filtering a toc_line from page_number and "................."
        # Example: "Introduction................................. 12 \n" is converted to "Introduction"
        toc_item.line.set_line(self.line.line.strip("\n ").rstrip(str(toc_item.page)).rstrip(". "))
        return toc_item


class TOCFeatureExtractor:
    end_with_num = re.compile(r"(.*[^\s.…])?[….\s]+(\d{1,3})(-\d{1,3})?$")
    window_size = 5
    titles = (
        "tableofcontents", "contents", "tableofcontentspage",  # english
        "содержание", "оглавление",  # russian
        "tabledesmatières", "tabledesmatieres", "sommaire",  # french
        "indice", "índice", "contenidos", "tabladecontenido"  # spanish
    )

    def get_toc(self, document: List[LineWithMeta], by_tag: Optional[str] = None) -> List[TocItem]:
        """
        Finds the table of contents in the given document using heuristic rules.

        :param document: document's textual lines
        :param by_tag: try to extract TocItems from textual lines by line.metadata.tag_hierarchy_level.line_type == by_tag.
                For better Toc extraction, a tocitem textual line (LineWithMeta) should have a 'tocitem_page' attribute in line.metadata,
                because the page number does not always match the page number in the table of contents element.
                For example:
                    line: 'Method implementation.....................45' converts to TocItem(line='Method implementation', page=45) where 'tocitem_page'==45

        :return:
            list of TocItem with (LineWithMeta) and page_number where it is located
        """
        if by_tag:
            return [
                TocItem(line=line, page=line.metadata.tocitem_page if hasattr(line.metadata, "tocitem_page") else line.metadata.page_id)
                for line in document if line.metadata.tag_hierarchy_level.line_type == by_tag
            ]

        probable_toc_lines, lines_have_page_number = self.__get_probable_toc(document)

        # filter too short TOCs
        if len(probable_toc_lines) <= self.window_size:
            return []

        unmerged_toc = self.__get_unmerged_toc(np.array(probable_toc_lines, dtype=object), np.array(lines_have_page_number, dtype=bool))
        merged_toc = self.__get_merged_multilines_toc(unmerged_toc)

        if len(merged_toc) > 6 and self.__check_page_order(merged_toc):
            return merged_toc
        return []

    def __get_merged_multilines_toc(self, result: List[TocItem or LineWithMeta]) -> List[TocItem]:
        # merge multiline toc items
        merged_toc: List[TocItem] = []
        cur_line: Optional[LineWithMeta] = None

        for line in result:
            # line may be a TocItem or LineWithMeta
            if isinstance(line, LineWithMeta):
                cur_line = line if cur_line is None else cur_line + line
            elif isinstance(line, TocItem):
                cur_line = line.line if cur_line is None else cur_line + line.line
                merged_toc.append(TocItem(line=cur_line, page=line.page))
                cur_line = None
            else:
                continue

        return merged_toc

    def __get_unmerged_toc(self, corrected_lines: np.ndarray, marks: np.ndarray) -> List[TocItem or LineWithMeta]:
        corrected_marks = []
        # fill empty space between toc items
        for idx in range(len(corrected_lines) - self.window_size):
            if sum(marks[:idx]) > 5 and not np.any(marks[idx: idx + self.window_size]):
                corrected_marks.extend([False] * (len(corrected_lines) - self.window_size - idx))
                break
            marked_before = np.any(marks[idx: idx + self.window_size]) and np.any(marks[:idx])
            marked_after = marks[idx] and np.any(marks[idx + 1: idx + self.window_size])
            corrected_marks.append(marked_before or marked_after)
        corrected_marks.extend([False] * self.window_size)
        result = list(corrected_lines[corrected_marks])
        return result

    def __get_probable_toc(self, document: List[LineWithMeta]) -> Tuple[List[TocItem or LineWithMeta], np.ndarray]:
        """
        :return:
            raw list of probable TOC items, can contain TocItem or LineWithMeta (in case the line is the continuation of a TOC item)
            list of lines_have_page_number - if the toc_line contains a page number or not
        """
        lines_have_page_number = []
        probable_toc_lines = []
        # First step: we check each line with regular expressions and find the TOC title and TOC items
        # We filter too short probable TOCs (< 6 TOC items) or too long probable TOC items (> 5 lines long)
        for line in document:
            line_text = line.line

            # check if the line is a TOC title
            probable_title = re.sub(r"[\s:]", "", line_text).lower()
            if probable_title in self.titles and sum(lines_have_page_number) < 6:  # filtering of short TOCs
                # clear current probable TOC
                probable_toc_lines = []
                lines_have_page_number = []
                continue

            # check if a line is a TOC item
            if not line_text.isspace() and not line_text.strip().isdigit():
                match = self.end_with_num.match(line_text.strip())
                if match:
                    # the line is a TOC item
                    probable_toc_lines.append(TocItem(line=line, page=int(match.group(2))))
                else:
                    # the line is the continuation of a TOC item
                    probable_toc_lines.append(line)
                lines_have_page_number.append(match is not None and len(line_text) > 5)
        return probable_toc_lines, np.array(lines_have_page_number, dtype=bool)

    def __check_page_order(self, corrected_result: List[TocItem]) -> bool:
        """
        check correctness of the result:

        CORRECT:
        Fist TOC item ..... 1
        Second TOC item ... 2
        Third TOC item .... 5

        INCORRECT:
        Fist TOC item ..... 10
        Second TOC item ... 2
        Third TOC item .... 5
        """
        assert len(corrected_result) > 1
        right_page_order = True
        prev_page = int(corrected_result[0].page)
        for item in corrected_result[1:]:
            if int(item.page) < prev_page:
                return False
            prev_page = int(item.page)
        return right_page_order

    def is_line_in_toc(self, document: List[LineWithMeta]) -> List[Optional[float]]:
        toc = self.get_toc(document=document) if len(document) > self.window_size else []
        result = []
        if len(toc) == 0:
            return [None] * len(document)
        for line in document:
            result.append(max(ratio(toc_line.line.line, line.line) for toc_line in toc))

        return result
