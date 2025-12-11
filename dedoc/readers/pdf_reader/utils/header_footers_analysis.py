import re
from collections import Counter
from typing import List, Optional, Tuple

import numpy as np

from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.utils.utils import similarity


class HeaderFooterDetector:
    """
    Class detects header and footer textual lines.
    The algorithm was implemented according to the article:

    `Lin X. Header and footer extraction by page association //Document Recognition and Retrieval X. – SPIE, 2003. – Т. 5010. – С. 164-171.`

    Algorithm's notes:

        1. For documents of 6 pages or more, lines on even and odd pages of the document are compared to detect alternating footers-headers.
           For documents of less than 6 pages, lines between adjacent pages (between even or odd pages) are compared.
           Therefore, alternating footers-headers will not be detected on documents of less than 6 pages.

        2. The algorithm analyzes the first 4 and last 4 lines on each page of the document and,
           by comparing lines across pages, identifies common footer-header patterns using Levenshtein similarity.

        3. For algorithm work, the document must have at least two pages of text.
           It is not an ML algorithm so it cannot work with just one page.

        4. The more pages, the better. Remember that the parameter `pages` limits the number of pages in a document.
    """

    def __init__(self) -> None:
        # 1 - first 4 weight for header, last 4 weight for footer
        self.weights = [1.0, 1.0, 0.85, 0.75, 0.75, 0.85, 1.0, 1.0]
        self.max_cnt_lines = len(self.weights)
        self.pattern_roman = r"\b[IVXLCDM]+\.?\b|\b[ivxlcdm]+\.?\b"
        self.pattern_digits = r"\d+"

    def detect(self, lines: List[List[LineWithLocation]], is_header_footer_threshold: float = 0.5) \
            -> Tuple[List[List[LineWithLocation]], List[List[LineWithLocation]], List[List[LineWithLocation]]]:

        scores = np.zeros(shape=(self.max_cnt_lines,), dtype=float)
        patterns = [[] for _ in range(self.max_cnt_lines)]
        cnt_cmpr = 0

        lines = self._strip_empty_lines(lines)
        page_cnt = len(lines)
        step = 2 if page_cnt > 5 else 1  # between one page for a big document (with changed header-footers)

        # 2 - formed comparison pattern for similarity
        for page in range(page_cnt):
            for line_index in range(self.max_cnt_lines // 2):
                if len(lines[page]) < self.max_cnt_lines:
                    patterns[line_index].append(None)
                    patterns[-line_index - 1].append(None)
                else:
                    patterns[line_index].append(self._replace_roman_and_digits_strict(lines[page][line_index].line))
                    patterns[-line_index - 1].append(self._replace_roman_and_digits_strict(lines[page][-line_index - 1].line))

        # 3 - calculate score of each header-footer line
        for page_one in range(page_cnt - step):
            page_two = page_one + step
            if len(lines[page_one]) < self.max_cnt_lines or len(lines[page_two]) < self.max_cnt_lines:
                continue
            # calc score for header
            for line_index in range(self.max_cnt_lines // 2):
                # calculation header score
                scores[line_index] += self.weights[line_index] * self._similarity(s1=patterns[line_index][page_one], s2=patterns[line_index][page_two])
                # calculation footer score
                similarity = self._similarity(s1=patterns[-line_index - 1][page_one], s2=patterns[-line_index - 1][page_two])
                scores[-line_index - 1] += self.weights[-line_index - 1] * similarity
            cnt_cmpr += 1

        scores /= cnt_cmpr
        is_footer_header = scores > is_header_footer_threshold

        # 4 - get the popular pattern from lines with high scores
        popular_patterns = self._get_popular_pattern(is_footer_header=is_footer_header, threshold=0.4 if step == 2 else 0.7, patterns=patterns)

        # 5 - delete only those lines which match with popular patterns
        headers, footers = [], []
        for page_id in range(page_cnt):
            headers.append([])
            footers.append([])

            for line_id in range(self.max_cnt_lines // 2):
                header = self._remove_header_footer(is_footer_header, popular_patterns, lines, page_id, line_id)
                if header:
                    lines[page_id][line_id] = None
                    headers[-1].append(header)

                footer = self._remove_header_footer(is_footer_header, popular_patterns, lines, page_id, -line_id - 1)
                if footer:
                    lines[page_id][-line_id - 1] = None
                    footers[-1].append(footer)

        # remove None-elements
        lines = [[line for line in page if line] for page in lines]

        return lines, headers, footers

    def _replace_roman_and_digits_strict(self, text: str) -> str:
        result = re.sub(self.pattern_roman, "@", text)
        result = re.sub(self.pattern_digits, "@", result)
        result = re.sub(r"@+", "@", result)

        return result.strip()

    def _similarity(self, s1: str, s2: str) -> float:
        if len(s1) == 0 or len(s2) == 0:
            return 0.0
        return similarity(s1, s2)

    def _strip_empty_lines(self, lines: List[List[LineWithLocation]]) -> List[List[LineWithLocation]]:
        reg_empty_string = re.compile(r"^\s*\n$")
        for page_id in range(len(lines)):
            line_id_begin_content = 0
            line_count = len(lines[page_id])
            while line_id_begin_content < line_count:
                if reg_empty_string.match(lines[page_id][line_id_begin_content].line) is None:
                    break
                line_id_begin_content += 1

            line_id_end_content = line_count - 1
            while line_id_end_content > 0:
                if reg_empty_string.match(lines[page_id][line_id_end_content].line) is None:
                    break
                line_id_end_content -= 1

            lines[page_id] = lines[page_id][line_id_begin_content:line_id_end_content + 1]

        return lines

    def _remove_header_footer(self, is_footer_header: np.ndarray,
                              popular_patterns: List[List[str]],
                              lines: List[List[LineWithLocation]],
                              page_id: int, line_id: int) -> Optional[LineWithLocation]:

        if not is_footer_header[line_id] or abs(line_id) >= len(lines[page_id]):
            return None
        for pattern in popular_patterns[line_id]:
            try:
                if re.match(pattern, self._replace_roman_and_digits_strict(lines[page_id][line_id].line)):
                    return lines[page_id][line_id]
            except re.error:
                pass

        return None

    def _get_popular_pattern(self, is_footer_header: np.ndarray, threshold: float, patterns: List[List[str]]) -> List[List[str]]:
        # Algorithm if header takes more than 40% of changed header-footer of doc
        #                       and more 70% in the doc with const header-footers
        #                        is_footer_header = [True,              False, False, False, True,            True         ]
        # Result example: popular_patterns_of_hf = [["header of company"],[], [], [], ["- @ -"], ["- @ -", "Robert's team"]]
        #                                          [------------ headers -------],[----------------footers-----------------]

        popular_patterns = [[] for _ in range(self.max_cnt_lines)]

        for num, pattern in enumerate(patterns):
            if not is_footer_header[num]:
                continue
            filter_pattern = [p for p in pattern if p]
            uniques = np.array(list(Counter(filter_pattern).keys()))
            freqs = np.array(list(Counter(filter_pattern).values())) / len(filter_pattern)
            popular_patterns[num].extend([pattern for num, pattern in enumerate(uniques) if freqs[num] > threshold])

        return popular_patterns
