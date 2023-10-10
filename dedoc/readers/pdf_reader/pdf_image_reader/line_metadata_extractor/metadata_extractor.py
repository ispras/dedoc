import re
from typing import List, Optional

import numpy as np
from numpy import median

from dedoc.data_structures.concrete_annotations.color_annotation import ColorAnnotation
from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.tables.location import Location
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.font_type_classifier import FontTypeClassifier


class LineMetadataExtractor:

    def __init__(self, default_spacing: int = 50, *, config: dict) -> None:
        self.config = config
        self.font_type_classifier = FontTypeClassifier()
        self.default_spacing = default_spacing

    def predict_annotations(self, page_with_lines: PageWithBBox) -> PageWithBBox:
        image_height, image_width, *_ = page_with_lines.image.shape
        page_with_fonts = self.font_type_classifier.predict_annotations(page_with_lines)

        for bbox in page_with_fonts.bboxes:
            font_size = self.__get_font_size(bbox, image_height)
            bbox.annotations.append(SizeAnnotation(start=0, end=len(bbox.text), value=str(font_size)))

        return page_with_fonts

    def extract_metadata_and_set_annotations(self, page_with_lines: PageWithBBox, call_classifier: bool = True) -> List[LineWithLocation]:
        """
        Take page with extracted lines and bboxes and determine line type as bold, italic, text alignment and so on
        Image should be rotated properly, it can be in grayscale or rgb
        @param page_with_lines: page with extracted lines (this can be done with tesseract)
        @param call_classifier: need or not predict bold classifier
        @return: Lines with meta-information
        """

        page_with_lines = self.__set_indentations(page=page_with_lines)
        if call_classifier:
            self.predict_annotations(page_with_lines)

        lines = []
        for bbox in page_with_lines.bboxes:
            lines.append(LineMetadataExtractor.get_line_with_meta(bbox=bbox))
            if page_with_lines.image.ndim == 3 and page_with_lines.image.shape[2] == 3:
                color_annotation = self.__get_color_annotation(bbox, page_with_lines.image)
                bbox.annotations.append(color_annotation)
        self.__add_spacing_annotations(lines)
        return lines

    @staticmethod
    def get_line_with_meta(bbox: TextWithBBox) -> LineWithLocation:
        metadata = LineMetadata(page_id=bbox.page_num, line_id=bbox.line_num)

        line = LineWithLocation(line=bbox.text,
                                metadata=metadata,
                                annotations=bbox.annotations,
                                uid=bbox.uid,
                                location=Location(bbox=bbox.bbox, page_number=bbox.page_num))
        return line

    @staticmethod
    def convert_pixels_into_indentation(indentation_width: int, image_width: int) -> int:
        # ref from http://officeopenxml.com/WPindentation.php
        # Values are in twentieths of a point: 1440 twips = 1 inch; 567 twips = 1 centimeter.
        indentation_per_cm = 567

        pixel2mm = 297 / image_width  # 297 mm it is height of A4 paper
        indentation_mm = indentation_width * pixel2mm
        indentation = int(indentation_mm / 10 * indentation_per_cm)

        return indentation

    def _get_text_left_bound(self, line_left_points: List[int]) -> int:
        """
            returns coordinates of left bound of the texts
            Algorithms: find the most two frequent left bounds and take the most left from them.
        """
        unique, counts = np.unique(line_left_points, axis=0, return_counts=True)
        count_sort_ind = np.argsort(-counts)
        unique_sort = unique[count_sort_ind]
        two_frequent_bound = unique_sort[:min(2, len(unique))]

        return min(two_frequent_bound)

    def __get_left_bound_of_text(self, page: PageWithBBox) -> Optional[int]:
        left_points = []
        for text_with_bbox in page.bboxes:
            left_points.append(text_with_bbox.bbox.x_top_left)
        if len(left_points) == 0:
            return None

        return self._get_text_left_bound(line_left_points=left_points)

    def __set_indentations(self, page: PageWithBBox) -> PageWithBBox:
        image_height, image_width, *_ = page.image.shape
        spaces_for_tab = "    "

        # TODO turn off for multicolumn pages (when we write columns-classifier). While turn on for all layout type.
        left_bound = self.__get_left_bound_of_text(page)
        if not left_bound:
            return page

        for text_with_bbox in page.bboxes:
            indentation_text = re.findall("^[ \t]+", text_with_bbox.text)
            width_space_indentation = 0
            width_per_char = text_with_bbox.bbox.width / len(text_with_bbox.text)

            if indentation_text:
                indentation_text = indentation_text[0].replace("\t", spaces_for_tab)
                width_space_indentation = len(indentation_text) * width_per_char

            indentation_width = (text_with_bbox.bbox.x_top_left - left_bound) + width_space_indentation

            if abs(indentation_width) < width_per_char:
                continue

            indentation = self.convert_pixels_into_indentation(indentation_width, image_width)
            text_with_bbox.annotations.append(IndentationAnnotation(start=0, end=len(text_with_bbox.text), value=str(indentation)))

        return page

    def __get_font_size(self, bbox: TextWithBBox, image_height: int) -> int:
        """
        determines the font size by the bbox size, return font size in typography point
        https://en.wikipedia.org/wiki/Point_(typography)
        we assume that page in A4 format and pt is equal 0.353 mm
        @param bbox: bbox of the text line
        @param image_height: height of the image in pixels
        @return: font size in points
        """
        pixel2mm = 297 / image_height  # 297 mm it is height of A4 paper
        font_size_mm = bbox.bbox.height * pixel2mm
        font_size_pt = font_size_mm / 0.353
        return round(font_size_pt)

    def __add_spacing_annotations(self, lines: List[LineWithLocation]) -> None:
        """
        add spacing annotations to lines. Assume that lines are in the proper order. This method work in place
        @param lines: list of line with meta
        @return:
        """
        median_bbox_size = median([line.location.bbox.height for line in lines])
        prev_line = None
        for line in lines:
            if prev_line is None or \
                    prev_line.location.page_number != line.location.page_number or \
                    prev_line.location.bbox.y_bottom_right >= line.location.bbox.y_top_left:
                space = self.default_spacing
            else:
                space = (line.location.bbox.y_top_left - prev_line.location.bbox.y_bottom_right)
                space = 100 * space / median_bbox_size
                space = int(space) if space > 1 else 1
            space = str(int(space))
            annotation = SpacingAnnotation(start=0, end=len(line.line), value=space)
            line.annotations.append(annotation)
            prev_line = line

    def __get_color_annotation(self, bbox_with_text: TextWithBBox, image: np.ndarray) -> ColorAnnotation:
        bbox = bbox_with_text.bbox

        image_slice = image[bbox.y_top_left: bbox.y_bottom_right, bbox.x_top_left: bbox.x_bottom_right, :]
        threshold = 245
        not_white = (image_slice[:, :, 0] < threshold) & (image_slice[:, :, 1] < threshold) & (image_slice[:, :, 2] < threshold)
        if not_white.sum() > 0:
            red, green, blue = [image_slice[not_white, i].mean() for i in range(3)]
        else:
            red, green, blue = 0, 0, 0
        return ColorAnnotation(start=0, end=len(bbox_with_text.text), red=red, green=green, blue=blue)
