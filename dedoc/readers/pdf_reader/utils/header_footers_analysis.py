import difflib
import re
from collections import Counter
from typing import List, Optional, Tuple

import numpy as np

from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation


def _get_pattern(s: str) -> str:
    return re.sub(r"\d+", "@", s.lower().strip())


def _similarity_with_replacement(s1: str, s2: str) -> float:
    if len(s1) == 0 or len(s2) == 0:
        return 0.0

    matcher = difflib.SequenceMatcher(None, s1, s2)
    ratio = matcher.ratio()
    return ratio


def _strip_empty_lines(lines: List[List[LineWithLocation]]) -> List[List[LineWithLocation]]:
    reg_empty_string = re.compile(r"^\s*\n$")
    for page_id in range(len(lines)):
        begin_content = False
        line_id_begin_content = 0
        while not begin_content and line_id_begin_content < len(lines[page_id]):
            if reg_empty_string.match(lines[page_id][line_id_begin_content].line) is None:
                begin_content = True
            else:
                line_id_begin_content += 1
        end_content = False
        line_id_end_content = len(lines[page_id]) - 1
        while not end_content and line_id_end_content > 0:
            if reg_empty_string.match(lines[page_id][line_id_end_content].line) is None:
                end_content = True
            else:
                line_id_end_content -= 1
        lines[page_id] = lines[page_id][line_id_begin_content:line_id_end_content + 1]

    return lines


def _remove_header_footer(is_footer_header: List[bool],
                          popular_patterns: List[List[str]],
                          lines: List[List[LineWithLocation]],
                          page_id: int, line_id: int) -> Optional[LineWithLocation]:

    if not is_footer_header[line_id] or abs(line_id) >= len(lines[page_id]):
        return None
    for pattern in popular_patterns[line_id]:
        try:
            if re.match(pattern, _get_pattern(lines[page_id][line_id].line)):
                return lines[page_id][line_id]
        except re.error:
            pass

    return None


def _get_popular_pattern(is_footer_header: List[bool], max_cnt_lines: int, threshold: float, patterns: List[List[str]]) -> List[List[str]]:
    # Algorithm if header takes more than 40% of changed header-footer of doc
    #                       and more 70% in the doc with const header-footers
    #                        is_footer_header = [True,              False, False, False, True,            True         ]
    # Result example: popular_patterns_of_hf = [["header of company"],[], [], [], ["- @ -"], ["- @ -", "Robert's team"]]
    #                                          [------------ headers -------],[----------------footers-----------------]

    popular_patterns = [[] for _ in range(max_cnt_lines)]

    for num, pattern in enumerate(patterns):
        if not is_footer_header[num]:
            continue
        filter_pattern = [p for p in pattern if p]
        uniques = np.array(list(Counter(filter_pattern).keys()))
        freqs = np.array(list(Counter(filter_pattern).values())) / len(filter_pattern)

        popular_patterns[num].extend([pattern for num, pattern in enumerate(uniques) if freqs[num] > threshold])

    return popular_patterns


def footer_header_analysis(lines: List[List[LineWithLocation]], threshold: float = 0.5) \
        -> Tuple[List[List[LineWithLocation]], List[List[LineWithLocation]], List[List[LineWithLocation]]]:
    # 1. инициализация весов, окна скольжения и скоров
    # first 4 weight for header, last 4 weight for footer
    weights = [1.0, 1.0, 0.85, 0.75, 0.75, 0.85, 1.0, 1.0]
    max_cnt_lines = 8
    scores = np.zeros(shape=(max_cnt_lines,), dtype=float)

    page_cnt = len(lines)
    patterns = [[] for _ in range(max_cnt_lines)]
    cnt_cmpr = 0

    lines = _strip_empty_lines(lines)
    if page_cnt > 6:
        step_hf = 2  # between one page for a big document (with changed header-footers)
    else:
        step_hf = 1  # analyze  each  neighbor page

    # 2 - formed comparison pattern for similarity
    for page in range(page_cnt):
        for line_index in range(max_cnt_lines // 2):
            if len(lines[page]) < max_cnt_lines:
                patterns[line_index].append(None)
                patterns[-line_index - 1].append(None)
            else:
                patterns[line_index].append(_get_pattern(lines[page][line_index].line))
                patterns[-line_index - 1].append(_get_pattern(lines[page][-line_index - 1].line))

    # 3 - calculate score of each header-footer line
    for page_one in range(page_cnt - step_hf):
        page_two = page_one + step_hf
        if len(lines[page_one]) < max_cnt_lines or len(lines[page_two]) < max_cnt_lines:
            continue
        # calc score for header
        for line_index in range(max_cnt_lines // 2):
            # calculation header score
            scores[line_index] += weights[line_index] * _similarity_with_replacement(s1=patterns[line_index][page_one], s2=patterns[line_index][page_two])

            # calculation footer score
            similarity = _similarity_with_replacement(s1=patterns[-line_index - 1][page_one], s2=patterns[-line_index - 1][page_two])
            scores[-line_index - 1] += weights[-line_index - 1] * similarity

        cnt_cmpr += 1

    scores /= cnt_cmpr
    is_footer_header = scores > threshold

    # 4 - get the popular pattern from lines with high scores
    popular_patterns = _get_popular_pattern(is_footer_header, max_cnt_lines, threshold=0.4 if step_hf == 2 else 0.7, patterns=patterns)
    # 5 - delete only those lines which match with popular patterns
    headers, footers = [], []

    for page_id in range(page_cnt):
        headers.append([])
        footers.append([])

        for line_id in range(max_cnt_lines // 2):

            header = _remove_header_footer(is_footer_header, popular_patterns, lines, page_id, line_id)
            if header:
                lines[page_id][line_id] = None
                headers[-1].append(header)

            footer = _remove_header_footer(is_footer_header, popular_patterns, lines, page_id, -line_id - 1)
            if footer:
                lines[page_id][-line_id - 1] = None
                footers[-1].append(footer)

    # remove None-elements
    lines = [[line for line in page if line] for page in lines]

    return lines, headers, footers
