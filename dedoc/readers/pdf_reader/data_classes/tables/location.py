from functools import total_ordering
from typing import Any, Dict, Optional

from dedocutils.data_structures import BBox


@total_ordering
class Location:
    def __init__(self, page_number: int, bbox: BBox, name: str = "", rotated_angle: float = 0.0, page_width: int = None, page_height: int = None) -> None:
        self.page_number = page_number
        self.page_width = page_width
        self.page_height = page_height
        self.bbox = bbox
        self.name = name
        # TODO put self.order (change LineWithLocation, PdfImageAttachment, ScanTable)
        self.rotated_angle = rotated_angle

    def shift(self, shift_x: int, shift_y: int) -> None:
        self.bbox.shift(shift_x, shift_y)

    def to_relative_bbox_dict(self) -> Optional[Dict]:
        if not self.page_height or not self.page_width:
            return None
        return self.bbox.to_relative_dict(self.page_width, self.page_height)

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
