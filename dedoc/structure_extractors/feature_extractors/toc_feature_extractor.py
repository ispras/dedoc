import re
from typing import List, Optional, Tuple, Union

import numpy as np
from Levenshtein._levenshtein import ratio

from dedoc.data_structures.line_with_meta import LineWithMeta


class TOCFeatureExtractor:
    end_with_num = re.compile(r"(.*[^\s.…])?[….\s]+(\d{1,3})(-\d{1,3})?$")
    window_size = 5
    titles = (
        "tableofcontents", "contents", "tableofcontentspage",  # english
        "содержание", "оглавление",  # russian
        "tabledesmatières", "tabledesmatieres", "sommaire",  # french
        "indice", "índice", "contenidos", "tabladecontenido"  # spanish
    )

    def get_toc(self, document: List[LineWithMeta]) -> List[dict]:
        """
        Finds the table of contents in the given document
        Returns:
            list of dictionaries with toc item and page number where it is located: {"line", "page"}
        """
        corrected_lines, marks = self.__get_probable_toc(document)

        marks = np.array(marks, dtype=bool)
        corrected_lines = np.array(corrected_lines, dtype=object)
        len_lines = corrected_lines.shape[0]

        # filter too short TOCs
        if len_lines <= self.window_size:
            return []
        result = self.__get_raw_result(corrected_lines, len_lines, marks)
        corrected_result = self.__get_corrected_result(result)

        if len(corrected_result) > 6 and self.__check_page_order(corrected_result):
            return corrected_result
        return []

    def __get_corrected_result(self, result: list) -> List[dict]:
        # merge multiline toc items
        corrected_result = []
        cur_line = None
        for line in result:
            # line may be a dict or LineWithMeta
            if isinstance(line, LineWithMeta):
                cur_line = line if cur_line is None else cur_line + line
                continue
            if not line["page"].isdigit():
                continue
            cur_line = line["line"] if cur_line is None else cur_line + line["line"]
            corrected_result.append({"line": cur_line, "page": line["page"]})
            cur_line = None
        return corrected_result

    def __get_raw_result(self, corrected_lines: np.ndarray, len_lines: int, marks: np.ndarray) -> list:
        corrected_marks = []
        # fill empty space between toc items
        for idx in range(len_lines - self.window_size):
            if sum(marks[:idx]) > 5 and not np.any(marks[idx: idx + self.window_size]):
                corrected_marks.extend([False] * (len_lines - self.window_size - idx))
                break
            marked_before = np.any(marks[idx: idx + self.window_size]) and np.any(marks[:idx])
            marked_after = marks[idx] and np.any(marks[idx + 1: idx + self.window_size])
            corrected_marks.append(marked_before or marked_after)
        corrected_marks.extend([False] * self.window_size)
        result = list(corrected_lines[corrected_marks])
        return result

    def __get_probable_toc(self, document: List[LineWithMeta]) -> Tuple[List[Union[dict, LineWithMeta]], List[bool]]:
        """
        returns:
            raw list of probable TOC items
            list of marks - if the line contains a page number or not
        """
        marks = []
        corrected_lines = []
        # First step: we check each line with regular expressions and find the TOC title and TOC items
        # We filter too short probable TOCs (< 6 TOC items) or too long probable TOC items (> 5 lines long)
        for line in document:
            line_text = line.line

            # check if the line is a TOC title
            probable_title = re.sub(r"[\s:]", "", line_text).lower()
            if probable_title in self.titles and sum(marks) < 6:  # filtering of short TOCs
                # clear current probable TOC
                corrected_lines = []
                marks = []
                continue

            # check if a line is a TOC item
            if not line_text.isspace() and not line_text.strip().isdigit():
                match = self.end_with_num.match(line_text.strip())
                if match:
                    # the line is a TOC item
                    corrected_lines.append({"line": line, "page": match.group(2)})
                else:
                    # the line is the continuation of a TOC item
                    corrected_lines.append(line)
                marks.append(match is not None and len(line_text) > 5)
        return corrected_lines, marks

    def __check_page_order(self, corrected_result: List[dict]) -> bool:
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
        prev_page = int(corrected_result[0]["page"])
        for item in corrected_result[1:]:
            if int(item["page"]) < prev_page:
                return False
            prev_page = int(item["page"])
        return right_page_order

    def is_line_in_toc(self, document: List[LineWithMeta]) -> List[Optional[float]]:
        toc = self.get_toc(document=document) if len(document) > self.window_size else []
        result = []
        if len(toc) == 0:
            return [None] * len(document)
        for line in document:
            result.append(max(ratio(toc_line["line"].line, line.line) for toc_line in toc))

        return result
