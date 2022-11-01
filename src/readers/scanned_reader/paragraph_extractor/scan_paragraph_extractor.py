from typing import List, Optional
import numpy as np

from src.readers.scanned_reader.data_classes.line_with_location import LineWithLocation
from src.utils.utils import list_get


class ScanParagraphExtractor(object):

    def extract(self, lines_with_links: List[LineWithLocation]) -> List[LineWithLocation]:
        if len(lines_with_links) <= 2:
            return lines_with_links

        indents = []
        for this_line, next_line in zip(lines_with_links[:-1], lines_with_links[1:]):
            if self._same_column(this_line, next_line):
                indent = self.__calculate_indent(next_line, this_line)
                indents.append(indent)
        if len(indents) < 10:
            return lines_with_links
        threshold = self.__get_threshold(indents)
        for line_id, line in enumerate(lines_with_links):
            previous_line = list_get(lines_with_links, line_id - 1)
            next_line = list_get(lines_with_links, line_id + 1)
            first_letter = list_get(line.line.strip(), 0, "")
            new_paragraph = first_letter.isupper() and self._is_new_paragraph(target_line=line,
                                                                              previous_line=previous_line,
                                                                              next_line=next_line,
                                                                              threshold=threshold)
            line.metadata.extend_other_fields({"new_paragraph": new_paragraph})
        return lines_with_links

    def __calculate_indent(self, next_line: LineWithLocation, this_line: LineWithLocation) -> float:
        indent = abs(this_line.location.bbox.x_top_left - next_line.location.bbox.x_top_left)
        indent /= this_line.location.bbox.width
        return indent

    def __get_threshold(self, indents: List[float]) -> float:
        assert len(indents) >= 10
        counters, values = np.histogram(indents, bins=int(len(indents) ** 0.5))
        counters_argsort = counters.argsort()
        return values[counters_argsort[1]] * 0.2 + 0.8 * values[counters_argsort[0]]

    def _same_column(self, line1: LineWithLocation, line2: LineWithLocation) -> bool:
        """
        check if two lines lay in the same column
        @param line1: first line
        @param line2: second line
        @return: True if line in the same column False otherwise
        """
        if line1.location.page_number != line2.location.page_number:
            return False
        bbox1 = line1.location.bbox
        bbox2 = line2.location.bbox
        # coordinates of the union of the bboxes
        union_left = min(bbox1.x_top_left, bbox2.x_top_left)
        union_right = max(bbox1.x_bottom_right, bbox2.x_bottom_right)
        assert union_right >= union_left
        if union_left == union_right:
            return False
        # coordinates of the intersection of the bboxes
        intersection_left = max(bbox1.x_top_left, bbox2.x_top_left)
        intersection_right = min(bbox1.x_bottom_right, bbox2.x_bottom_right)
        iou = (intersection_right - intersection_left) / (union_right - union_left)
        return iou > 0.60

    def _is_new_paragraph(self,
                          target_line: LineWithLocation,
                          previous_line: Optional[LineWithLocation],
                          next_line: Optional[LineWithLocation],
                          threshold: float) -> bool:
        """
        Check if new target_line is starts new paragraph. Compare indent with previous and next line and return true if
        indent / target_line.width > threshold
        @param target_line:
        @param previous_line:
        @param next_line:
        @param threshold:
        @return:
        """
        if self.__compare_pair(target_line=target_line, other_line=previous_line, threshold=threshold):
            return True
        if self.__compare_pair(target_line=target_line, other_line=next_line, threshold=threshold):
            return True
        return False

    def __compare_pair(self, target_line: LineWithLocation, other_line: LineWithLocation, threshold: float) -> bool:
        if other_line is not None and self._same_column(target_line, other_line):
            indent = self.__calculate_indent(target_line, other_line)
            if indent > threshold:
                return True
        return False
