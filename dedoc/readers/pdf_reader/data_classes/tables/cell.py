import uuid
from collections import OrderedDict
from typing import Optional

from dedoc.data_structures.bbox import BBox


class Cell:

    @staticmethod
    def copy_from(cell: "Cell",
                  x_top_left: Optional[int] = None,
                  x_bottom_right: Optional[int] = None,
                  y_top_left: Optional[int] = None,
                  y_bottom_right: Optional[int] = None) -> "Cell":
        x_top_left = cell.x_top_left if x_top_left is None else x_top_left
        x_bottom_right = cell.x_bottom_right if x_bottom_right is None else x_bottom_right
        y_top_left = cell.y_top_left if y_top_left is None else y_top_left
        y_bottom_right = cell.y_bottom_right if y_bottom_right is None else y_bottom_right
        return Cell(x_top_left=x_top_left,
                    x_bottom_right=x_bottom_right,
                    y_top_left=y_top_left,
                    y_bottom_right=y_bottom_right,
                    id_con=cell.id_con,
                    text=cell.text,
                    is_attribute=cell.is_attribute,
                    is_attribute_required=cell.is_attribute_required,
                    rotated_angle=cell.rotated_angle,
                    uid=cell.cell_uid,
                    contour_coord=cell.con_coord)

    def __init__(self,
                 x_top_left: int,
                 x_bottom_right: int,
                 y_top_left: int,
                 y_bottom_right: int,
                 id_con: int = -1,
                 text: str = "",
                 is_attribute: bool = False,
                 is_attribute_required: bool = False,
                 rotated_angle: int = 0,
                 uid: str = None,
                 contour_coord: BBox = BBox(0, 0, 0, 0)) -> None:
        assert x_top_left <= x_bottom_right
        assert y_top_left <= y_bottom_right
        self.x_top_left = x_top_left
        self.x_bottom_right = x_bottom_right
        self.y_top_left = y_top_left
        self.y_bottom_right = y_bottom_right
        self.id_con = id_con
        if not isinstance(text, str):
            raise ValueError("get {} ({}) instead of text".format(text.__class__, text))
        self.text = text
        self.is_attribute = is_attribute
        self.is_attribute_required = is_attribute_required
        self.rotated_angle = rotated_angle
        self.cell_uid = "cell_{}".format(uuid.uuid1()) if uid is None else uid
        self.colspan = 1
        self.rowspan = 1
        self.invisible = False
        self.con_coord = contour_coord

    def __str__(self) -> str:
        return "Cell((cs={}, rs={}, {})".format(self.colspan, self.rowspan, self.text)

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def width(self) -> int:
        return self.x_bottom_right - self.x_top_left

    @property
    def height(self) -> int:
        return self.y_bottom_right - self.y_top_left

    def to_dict(self) -> dict:
        cell_dict = OrderedDict()
        cell_dict["text"] = self.text
        cell_dict["is_attribute"] = self.is_attribute
        cell_dict["colspan"] = self.colspan
        cell_dict["rowspan"] = self.rowspan
        cell_dict["invisible"] = self.invisible

        return cell_dict

    def set_rotated_angle(self, rotated_angle: int) -> None:
        self.rotated_angle = rotated_angle
