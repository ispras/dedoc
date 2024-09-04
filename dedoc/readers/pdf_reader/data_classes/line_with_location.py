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

    @staticmethod
    def shift_line_with_location(line_with_location: "LineWithLocation", shift_x: int, shift_y: int, image_width: int, image_height: int) -> "LineWithLocation":
        from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
        from dedocutils.data_structures import BBox
        new_annotations = []
        for i_ann, annotation in enumerate(line_with_location.annotations):
            if line_with_location.annotations[i_ann].name != "bounding box":
                new_annotations.append(annotation)
            else:
                bbox, page_width, page_height = BBoxAnnotation.get_bbox_from_value(annotation.value)
                new_bbox = BBox.shift_bbox(bbox, shift_x, shift_y)
                new_bbox_annotation = BBoxAnnotation(start=annotation.start,
                                                     end=annotation.end,
                                                     value=new_bbox,
                                                     page_width=image_width,
                                                     page_height=image_height)
                new_annotations.append(new_bbox_annotation)
        new_location = Location.shift_location(line_with_location.location, shift_x, shift_y)
        return LineWithLocation(line=line_with_location.line,
                                metadata=line_with_location.metadata,
                                annotations=new_annotations,
                                location=new_location,
                                uid=line_with_location.uid,
                                order=line_with_location.order)

    def __repr__(self) -> str:
        parent_repr = super().__repr__()
        return parent_repr.replace("LineWithMeta", "LineWithLocation")

    def __str__(self) -> str:
        return self.__repr__()
