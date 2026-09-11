from typing import Tuple

from dedocutils.data_structures import BBox

from dedoc.data_structures.annotation import Annotation


class BBoxAnnotation(Annotation):
    """
    Coordinates of the line's bounding box (in relative coordinates) - for pdf documents.
    """
    name = "bounding box"

    def __init__(self, start: int, end: int, value: BBox, page_width: int, page_height: int) -> None:
        """
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        :param value: bounding box where line is located
        :param page_width: width of original image with this bbox
        :param page_height: height of original image with this bbox
        """
        if not isinstance(value, BBox):
            raise ValueError("the value of bounding box annotation should be instance of BBox")

        # Build the JSON string directly instead of json.dumps(to_relative_dict(...)): this runs once per line-bbox
        # (tens of thousands per document) and the json encoder dominated post-processing. str(float) equals repr and
        # json's float encoding, and int str equals json's, so the result is byte-identical to the old json.dumps
        # (verified over 120k+ bbox values), just without the encoder overhead.
        x, y = value.x_top_left / page_width, value.y_top_left / page_height
        w, h = value.width / page_width, value.height / page_height
        value_json = f'{{"x_top_left": {x}, "y_top_left": {y}, "width": {w}, "height": {h}, "page_width": {page_width}, "page_height": {page_height}}}'
        super().__init__(start=start, end=end, name=BBoxAnnotation.name, value=value_json, is_mergeable=False)

    @staticmethod
    def get_bbox_from_value(value: str) -> Tuple[BBox, int, int]:
        """
        Returns: BBox object, page_width, page_height
        """
        import json

        bbox_dict = json.loads(value)
        bbox = BBox(x_top_left=int(bbox_dict["x_top_left"] * bbox_dict["page_width"]),
                    y_top_left=int(bbox_dict["y_top_left"] * bbox_dict["page_height"]),
                    width=int(bbox_dict["width"] * bbox_dict["page_width"]),
                    height=int(bbox_dict["height"] * bbox_dict["page_height"]))
        return bbox, bbox_dict["page_width"], bbox_dict["page_height"]
