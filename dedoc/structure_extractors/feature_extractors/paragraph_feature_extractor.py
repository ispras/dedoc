from collections import defaultdict, deque
from typing import Iterator, List, Optional, Tuple

import pandas as pd
from _operator import attrgetter
from dedocutils.data_structures import BBox
from pandas import DataFrame

from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TocItem
from dedoc.utils.utils import list_get


class ParagraphFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self, *, config: dict = None) -> None:  # noqa
        super().__init__()
        self.config = config if config is not None else {}
        self.list_feature_extractor = ListFeaturesExtractor()

    def parameters(self) -> dict:
        return {}

    def __process_document(self, document: List[LineWithMeta]) -> pd.DataFrame:
        _, list_features_df = self.list_feature_extractor.one_document(document)
        list_features_df["list_item"] = self._list_features(document)

        one_line_features_dict = defaultdict(list)
        for line_id, line in enumerate(document):
            prev_line = list_get(document, line_id - 1)
            next_line = list_get(document, line_id + 1)

            for feature_name, feature in self._one_line_features(line, prev_line, next_line):
                one_line_features_dict[feature_name].append(feature)

        one_doc_features_df = pd.DataFrame(one_line_features_dict)
        one_doc_features_df = self.__normalize_features(one_doc_features_df)

        # result_matrix = self.prev_next_line_features(one_doc_features_df, 1, 1)
        result_matrix = pd.concat([one_doc_features_df, list_features_df], axis=1)

        return result_matrix

    def __normalize_features(self, features_df: DataFrame) -> DataFrame:
        normalize_columns = (
            "distance_prev", "distance_next", "height", "height_next", "height_prev", "indent", "indent_right", "indent_prev_right", "indent_next",
            "indent_prev"
        )
        for column in normalize_columns:
            if column in features_df.columns:
                features_df[column] = self._get_features_quantile(features_df[column])

        return features_df

    def transform(self, documents: List[List[LineWithMeta]], toc_lines: Optional[List[List[TocItem]]] = None) -> pd.DataFrame:
        result_matrix = pd.concat([self.__process_document(document) for document in documents], ignore_index=True)
        features = sorted(result_matrix.columns)
        return result_matrix[features].astype(float)

    def _one_line_features(self, line: LineWithMeta, prev_line: Optional[LineWithMeta], next_line: Optional[LineWithMeta]) -> Iterator[Tuple[str, int]]:
        bbox, page_width = self._get_bbox(line)
        prev_line_bbox, _ = self._get_bbox(prev_line)
        next_line_bbox, _ = self._get_bbox(next_line)
        prev_indent_queue = deque([], maxlen=5)
        if bbox is not None:
            prev_indent_queue.append(bbox.x_top_left)

        yield "indent", bbox.x_top_left if bbox else None
        yield "indent_prev", self._relative_indent(bbox, prev_line_bbox) if bbox else None
        yield "indent_next", self._relative_indent(next_line_bbox, bbox) if bbox else None
        yield "indent_right", bbox.x_bottom_right if bbox else None
        yield "indent_prev_right", self._relative_indent(bbox, prev_line_bbox, left=False) if bbox else None

        yield "intersection_next", self._intersection(next_line_bbox, bbox) if bbox else None
        yield "intersection_prev", self._intersection(prev_line_bbox, bbox) if bbox else None
        yield "prev_text_lens", len(prev_line.line) if prev_line else None
        yield "text_lens", len(line.line)

        if prev_line:
            yield "upper_letters_percent_prev", self._get_percent_upper_letters(line)
        else:
            yield "upper_letters_percent_prev", None

        caps = self._get_percent_upper_letters(line)
        yield "upper_letters_percent", caps
        yield "is_capitalized", int(caps == 1.0)

        bold = self._get_bold_percent(line)
        yield "is_bold_changed", int(bold == 1.0) != int(self._get_bold_percent(prev_line) == 1.0) if prev_line else None
        yield "is_bold_changed_next", int(self._get_bold_percent(line) == 1.0) != int(self._get_bold_percent(next_line) == 1.0) if next_line else None

        if prev_line:
            _, _, _, color_dispersion_cur = list(self._get_color(prev_line))
            _, _, _, color_dispersion_prev = list(self._get_color(line))
            yield "color_dispersion_diff", abs(color_dispersion_cur[1] - color_dispersion_prev[1])
        else:
            yield "color_dispersion_diff", None

        yield "distance_prev", bbox.y_top_left - prev_line_bbox.y_bottom_right if prev_line_bbox and bbox else None
        yield "distance_next", next_line_bbox.y_top_left - bbox.y_bottom_right if next_line_bbox and bbox else None

        yield "height", bbox.height if bbox else None
        yield "height_next", bbox.height / (next_line_bbox.height + 1) if (next_line_bbox and bbox) else None
        yield "height_prev", bbox.height / (prev_line_bbox.height + 1) if (prev_line_bbox and bbox) else None

    def _relative_indent(self, this_bbox: Optional[BBox], prev_bbox: Optional[BBox], left: bool = True) -> Optional[float]:
        if this_bbox is None or prev_bbox is None:
            return None
        elif left:
            return this_bbox.x_top_left - prev_bbox.x_top_left
        else:
            return this_bbox.x_bottom_right - prev_bbox.x_bottom_right

    def _relative_indent_new(self, this_bbox: Optional[BBox], prev_bbox: Optional[BBox], page_width: Optional[int], left: bool = True) -> Optional[float]:
        if this_bbox is None or prev_bbox is None or page_width is None:
            return None
        elif left:
            return min(this_bbox.x_top_left - prev_bbox.x_top_left / page_width, 1.0)
        else:
            return min(this_bbox.x_bottom_right - prev_bbox.x_bottom_right / page_width, 1.0)

    def _diff_left_right_indent(self, this_box: Optional[BBox], page_width: Optional[int]) -> Optional[float]:
        if this_box is None or page_width is None:
            return None
        left = this_box.x_top_left
        right = page_width - this_box.x_bottom_right
        diff = abs(left - right) / page_width
        return diff

    def _intersection(self, this_bbox: Optional[BBox], that_bbox: Optional[BBox]) -> Optional[float]:
        if this_bbox is None or that_bbox is None:
            return None
        if this_bbox.x_top_left >= that_bbox.x_bottom_right or that_bbox.x_top_left >= this_bbox.x_bottom_right:
            return 0
        union_left = min(this_bbox.x_top_left, that_bbox.x_top_left)
        union_right = max(this_bbox.x_bottom_right, that_bbox.x_bottom_right)

        intersection_left = max(this_bbox.x_top_left, that_bbox.x_top_left)
        intersection_right = min(this_bbox.x_bottom_right, that_bbox.x_bottom_right)
        if union_left <= union_right:
            return 0
        else:
            return (intersection_right - intersection_left) / (union_right - union_left)

    def _get_bbox(self, line: Optional[LineWithMeta]) -> Tuple[Optional[BBox], Optional[int]]:
        if line is None:
            return None, None
        if isinstance(line, LineWithLocation):
            return line.location.bbox, None

        bboxes_w_h = [BBoxAnnotation.get_bbox_from_value(bbox.value) for bbox in line.annotations if bbox.name == BBoxAnnotation.name]
        bboxes, pages_width, _ = zip(*bboxes_w_h)
        page_width = pages_width[0] if len(pages_width) > 0 and pages_width[0] > 1 else None
        if len(bboxes) > 1:
            line_bbox = BBox.from_two_points(
                top_left=(min(bboxes, key=attrgetter("x_top_left")).x_top_left, min(bboxes, key=attrgetter("y_top_left")).y_top_left),
                bottom_right=(max(bboxes, key=attrgetter("x_bottom_right")).x_bottom_right, max(bboxes, key=attrgetter("y_bottom_right")).y_bottom_right)
            )
            return line_bbox, page_width
        else:
            return bboxes[0], page_width
