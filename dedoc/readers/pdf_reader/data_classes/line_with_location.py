from typing import List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.tables.location import Location


class LineWithLocation(LineWithMeta):

    def __init__(self, line: str, metadata: LineMetadata, annotations: List[Annotation], location: Location, uid: str = None, order: int = -1) -> None:
        self.location = location
        self.order = order
        super().__init__(line, metadata, annotations, uid)

    def shift(self, shift_x: int, shift_y: int, image_width: int, image_height: int) -> None:
        import json
        from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
        for i_ann, annotation in enumerate(self.annotations):
            if self.annotations[i_ann].name == "bounding box":
                bbox, page_width, page_height = BBoxAnnotation.get_bbox_from_value(annotation.value)
                bbox.shift(shift_x, shift_y)
                self.annotations[i_ann].value = json.dumps(bbox.to_relative_dict(image_width, image_height))
        self.location.shift(shift_x, shift_y)

    def __repr__(self) -> str:
        parent_repr = super().__repr__()
        return parent_repr.replace("LineWithMeta", "LineWithLocation")

    def __str__(self) -> str:
        return self.__repr__()
