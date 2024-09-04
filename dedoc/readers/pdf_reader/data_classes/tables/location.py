from functools import total_ordering
from typing import Any, Dict

from dedocutils.data_structures import BBox


@total_ordering
class Location:
    def __init__(self, page_number: int, bbox: BBox, name: str = "", rotated_angle: float = 0.0) -> None:
        self.page_number = page_number
        self.bbox = bbox
        self.name = name
        self.rotated_angle = rotated_angle

    @staticmethod
    def shift_location(location: "Location", shift_x: int, shift_y: int):
        return Location(page_number=location.page_number,
                        bbox=BBox.shift_bbox(location.bbox, shift_x, shift_y),
                        name=location.name,
                        rotated_angle=location.rotated_angle)

    def to_dict(self) -> Dict[str, Any]:
        from collections import OrderedDict

        res = OrderedDict()
        res["page_number"] = self.page_number
        res["bbox"] = self.bbox.to_dict()  # [x_begin, y_begin, width, height]
        res["name"] = self.name
        res["rotated_angle"] = self.rotated_angle
        return res

    def __eq__(self, other: "Location") -> bool:
        return (self.page_number, self.bbox.y_bottom_right) == (other.page_number, other.bbox.y_bottom_right)

    def __lt__(self, other: "Location") -> bool:
        return (self.page_number, self.bbox.y_bottom_right) < (other.page_number, other.bbox.y_bottom_right)
