import math
from collections import OrderedDict
from functools import total_ordering
from typing import Tuple, Dict, Any

from dedoc.data_structures.bbox import BBox


@total_ordering
class Location:
    def __init__(self, page_number: int, bbox: BBox, name: str = "") -> None:
        self.page_number = page_number
        self.bbox = bbox
        self.name = name

    def rotate_coordinates(self, angle_rotate: float, image_shape: Tuple[int]) -> None:
        xb, yb = self.bbox.x_top_left, self.bbox.y_top_left
        # TODO check!!! was xe, ye = self.bbox.x_begin + self.bbox.width, self.bbox.x_begin + self.bbox.height
        xe, ye = self.bbox.x_bottom_right, self.bbox.y_bottom_right  # self.bbox.x_top_left + self.bbox.height
        rad = angle_rotate * math.pi / 180

        bbox_xb = min((int(float(xb) * math.cos(rad) - float(yb) * math.sin(rad))), image_shape[1])
        bbox_yb = min((int(float(yb) * math.cos(rad) + float(xb) * math.sin(rad))), image_shape[0])
        bbox_xe = min((int(float(xe) * math.cos(rad) - float(ye) * math.sin(rad))), image_shape[1])
        bbox_ye = min((int(float(ye) * math.cos(rad) + float(xe) * math.sin(rad))), image_shape[0])
        bbox_new = BBox(bbox_xb, bbox_yb, bbox_xe - bbox_xb, bbox_ye - bbox_yb)

        self.bbox = bbox_new

    def to_dict(self) -> Dict[str, Any]:
        res = OrderedDict()
        res["page_number"] = self.page_number
        res["bbox"] = self.bbox.to_dict()  # [x_begin, y_begin, width, height]
        res["name"] = self.name
        return res

    def __eq__(self, other: "Location") -> bool:
        return (self.page_number, self.bbox.y_bottom_right) == (other.page_number, other.bbox.y_bottom_right)

    def __lt__(self, other: "Location") -> bool:
        return (self.page_number, self.bbox.y_bottom_right) < (other.page_number, other.bbox.y_bottom_right)
