import logging
from collections import defaultdict, deque
from typing import Dict, List, Union

from dedocutils.data_structures import BBox

from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.location import Location
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable


class LineObjectLinker:

    def __init__(self, *, config: dict) -> None:
        """
        link page object (as table, image etc) with text line. Add annotation about page object location to line
        """
        self.n_lines = 5
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def link_objects(self, lines: List[LineWithLocation], tables: List[ScanTable], images: List[PdfImageAttachment]) -> List[LineWithLocation]:
        """
        add annotations to lines. Add annotations with links to the tables, images and other objects. Add spacing links
        to the lines
        @param lines:
        @param tables:
        @param images:
        @return:
        """
        if len(lines) == 0:
            metadata = LineMetadata(tag_hierarchy_level=HierarchyLevel.create_raw_text(), page_id=0, line_id=0)
            lines = [LineWithLocation(line="", metadata=metadata, annotations=[], location=Location(page_number=0, bbox=BBox(0, 0, 1, 1)))]
        last_page_line = self._get_last_page_line(lines)
        all_objects = list(lines + tables + images)
        all_objects.sort(key=lambda o: (o.order, o.location))
        objects_with_line_candidate = defaultdict(dict)
        self._add_lines(all_objects, "previous_lines", objects_with_line_candidate)
        self._add_lines(all_objects[::-1], "next_lines", objects_with_line_candidate)

        for object_with_lines in objects_with_line_candidate.values():
            page_object = object_with_lines["object"]
            best_line = self._find_closest_line(page_object=page_object,
                                                lines_before=object_with_lines["previous_lines"],
                                                lines_after=object_with_lines["next_lines"],
                                                last_page_line=last_page_line)
            if isinstance(page_object, ScanTable):
                annotation = TableAnnotation(name=page_object.uid, start=0, end=len(best_line.line))
            elif isinstance(page_object, PdfImageAttachment):
                annotation = AttachAnnotation(attach_uid=page_object.uid, start=0, end=len(best_line.line))
            else:
                self.logger.warning(f"Unsupported page object type {page_object}")
                if self.config.get("debug_mode", False):
                    raise Exception(f"Unsupported page object type {page_object}")
            best_line.annotations.append(annotation)  # noqa
        return lines

    def _add_lines(self, all_objects: List[Union[LineWithLocation, ScanTable, PdfImageAttachment]], lines_key: str, objects_with_line_candidate: dict) -> None:
        lines_deque = deque(maxlen=self.n_lines)
        for page_object in all_objects:
            if isinstance(page_object, LineWithLocation):
                lines_deque.append(page_object)
            else:
                lines = [line for line in lines_deque]
                objects_with_line_candidate[page_object.uid]["object"] = page_object
                objects_with_line_candidate[page_object.uid][lines_key] = lines

    def _find_closest_line(self,
                           page_object: Union[ScanTable, PdfImageAttachment],
                           lines_before: List[LineWithLocation],
                           lines_after: List[LineWithLocation],
                           last_page_line: Dict[int, LineWithLocation]) -> LineWithLocation:
        """
        choose best line to link with given page object. Take into account only a few lines before and after object
        @param page_object: some object as table or image
        @param lines_before: self.n_lines before the given object
        @param lines_after: self.n_lines after object
        @return: best line to link with object
        """
        all_lines = lines_before + lines_after
        line_on_same_page = [line for line in all_lines if line.location.page_number == page_object.location.page_number]
        # no one line on the same page
        if len(line_on_same_page) == 0:
            previous_page_id = page_object.location.page_number - 1
            if previous_page_id in last_page_line:
                return last_page_line[previous_page_id]
            lines_prev_page = [line for line in all_lines if line.location < page_object.location]
            if len(lines_prev_page) > 0:
                return max(lines_prev_page, key=lambda line: line.location)
            else:
                return min(all_lines, key=lambda line: line.location)
        line_with_distance = [(self._distance_bboxes(line, page_object.location.bbox), line) for line in line_on_same_page]
        return min(line_with_distance, key=lambda t: t[0])[1]

    @staticmethod
    def _distance_bboxes(line: LineWithLocation, object_bbox: BBox) -> float:
        """
        calculate the "distance between two bboxes"
        """
        line_bbox = line.location.bbox
        vertical_distance_abs = min(abs(line_bbox.y_top_left - object_bbox.y_bottom_right), abs(line_bbox.y_bottom_right - object_bbox.y_top_left))
        vertical_distance = vertical_distance_abs / (object_bbox.height + 1e-3)

        # calculate horizontal intersection
        left = max(line_bbox.x_top_left, object_bbox.x_top_left)
        right = min(line_bbox.x_bottom_right, object_bbox.x_bottom_right)
        horizontal_intersection = (right - left) / line_bbox.width if right > left else 0
        special_distance = 0
        text = line.line.lower().strip()
        if len(text) == 0:
            special_distance += 0.5
        elif text.startswith(("таблица ", "таб. ", "table ")):
            special_distance -= 0.5

        assert horizontal_intersection >= 0
        return vertical_distance - horizontal_intersection + special_distance

    def _get_last_page_line(self, lines: List[LineWithLocation]) -> Dict[int, LineWithLocation]:
        result = {}
        for line in lines:
            result[line.location.page_number] = line
        return result
