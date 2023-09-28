import json
from collections import deque
from typing import Any, List, Optional

import numpy as np
import pandas as pd
from dedocutils.data_structures import BBox

from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.utils.utils import list_get


class ParagraphFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self, *, config: dict = None, **kwargs: Any) -> None:  # noqa
        super().__init__()
        self.config = config if config is not None else {}

    def parameters(self) -> dict:
        return {}

    def fit(self, lines: List[List[LineWithMeta]], labels: List[str] = None) -> "ParagraphFeatureExtractor":
        return self

    def fit_transform(self, lines: List[List[LineWithMeta]], labels: List[str] = None) -> pd.DataFrame:
        self.fit(lines=lines, labels=labels)
        return self.transform(lines)

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        results = []
        for document in documents:
            queue = deque([], maxlen=5)
            for line_id, line in enumerate(document):
                result = {}
                bbox = self._get_bbox(line)
                if bbox is not None:
                    queue.append(bbox.x_top_left)
                result["local_order"] = None if bbox is None else np.searchsorted(sorted(queue), bbox.x_top_left)
                prev_line = list_get(document, line_id - 1)
                prev_line_bbox = self._get_bbox(prev_line)
                next_line = list_get(document, line_id + 1)
                next_line_bbox = self._get_bbox(next_line)
                result["indent"] = bbox.x_top_left if bbox else None
                result["indent_right"] = bbox.x_bottom_right if bbox else None

                result["indent_prev"] = self._relative_indent(bbox, prev_line_bbox) if bbox else None
                result["indent_prev_right"] = self._relative_indent(bbox, prev_line_bbox, left=False) if bbox else None
                result["indent_next"] = self._relative_indent(next_line_bbox, bbox) if bbox else None

                result["intersection_next"] = self._intersection(next_line_bbox, bbox) if bbox else None
                result["intersection_prev"] = self._intersection(prev_line_bbox, bbox) if bbox else None
                first_letter = list_get(line.line, 0, "")
                result["is_capitalized"] = int(first_letter.isupper() or not first_letter.isalpha())
                result["is_capitalized"] = int(line.line.isupper())

                if prev_line_bbox is None or bbox is None:
                    result["distance_prev"] = None
                else:
                    result["distance_prev"] = (bbox.y_top_left - prev_line_bbox.y_bottom_right)

                if next_line_bbox is None or bbox is None:
                    result["distance_next"] = None
                else:
                    result["distance_next"] = (next_line_bbox.y_top_left - bbox.y_bottom_right)

                result["height"] = bbox.height if bbox else None
                result["height_next"] = bbox.height / (next_line_bbox.height + 1) if (next_line_bbox and bbox) else None
                result["height_prev"] = bbox.height / (prev_line_bbox.height + 1) if (prev_line_bbox and bbox) else None
                results.append(result)
        df_results = pd.DataFrame(results)

        # TODO replace with quantilies
        quantile_columns = ("distance_prev", "distance_next", "height_next", "height_prev", "indent", "indent_right")
        for col in quantile_columns:
            df_results[col] = self._get_features_quantile(df_results[col])

        for col in df_results.columns:
            if col not in quantile_columns:
                df_results[col] /= (df_results[col].max() - df_results[col].min() + 1)
        return df_results[sorted(df_results.columns)]

    def _relative_indent(self, this_bbox: Optional[BBox], prev_bbox: Optional[BBox], left: bool = True) -> Optional[float]:
        if this_bbox is None or prev_bbox is None:
            return None
        elif left:
            return this_bbox.x_top_left - prev_bbox.x_top_left
        else:
            return this_bbox.x_bottom_right - prev_bbox.x_bottom_right

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

    def _get_bbox(self, line: Optional[LineWithMeta]) -> Optional[BBox]:
        if line is None:
            return None
        if isinstance(line, LineWithLocation):
            return line.location.bbox
        bbox = [bbox for bbox in line.annotations if bbox.name == BBoxAnnotation.name]
        if len(bbox) > 0:
            d = json.loads(bbox[0].value)
            return BBox(x_top_left=d["x_top_left"], y_top_left=d["y_top_left"], width=d["width"], height=d["height"])
        return None
