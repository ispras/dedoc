import uuid
from typing import List, Optional

from dedocutils.data_structures import BBox

from dedoc.data_structures import BBoxAnnotation
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.line_with_meta import LineWithMeta


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
                    lines=cell.lines,
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
                 lines: Optional[List[LineWithMeta]] = None,
                 is_attribute: bool = False,
                 is_attribute_required: bool = False,
                 rotated_angle: int = 0,
                 uid: str = None,
                 contour_coord: Optional[BBox] = None) -> None:

        assert x_top_left <= x_bottom_right
        assert y_top_left <= y_bottom_right
        self.x_top_left = x_top_left
        self.x_bottom_right = x_bottom_right
        self.y_top_left = y_top_left
        self.y_bottom_right = y_bottom_right
        self.id_con = id_con
        self.lines = [] if lines is None else lines
        self.is_attribute = is_attribute
        self.is_attribute_required = is_attribute_required
        self.rotated_angle = rotated_angle
        self.cell_uid = f"cell_{uuid.uuid1()}" if uid is None else uid
        self.colspan = 1
        self.rowspan = 1
        self.invisible = False
        self.con_coord = contour_coord or BBox(0, 0, 0, 0)

    def __str__(self) -> str:
        return f"Cell((cs={self.colspan}, rs={self.rowspan}, {self.get_text()})"

    def get_text(self) -> str:
        return "\n".join([line.line for line in self.lines])

    def get_annotations(self) -> List[Annotation]:
        return LineWithMeta.join(self.lines, delimiter="\n").annotations

    def change_lines_boxes_page_width_height(self, new_page_width: int, new_page_height: int) -> None:
        for i_line, _ in enumerate(self.lines):
            for i_ann, annotation in enumerate(self.lines[i_line].annotations):
                if annotation.name != "bounding box":
                    continue

                bbox, page_width, page_height = BBoxAnnotation.get_bbox_from_value(annotation.value)
                k_w = new_page_width / page_width
                k_h = new_page_height / page_height
                new_bbox = BBox(x_top_left=int(bbox.x_top_left * k_w), y_top_left=int(bbox.y_top_left * k_h),
                                width=int(bbox.width * k_w), height=int(bbox.height * k_h))

                self.lines[i_line].annotations[i_ann] = BBoxAnnotation(start=annotation.start,
                                                                       end=annotation.end,
                                                                       value=new_bbox,
                                                                       page_width=new_page_width,
                                                                       page_height=new_page_height)

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def width(self) -> int:
        return self.x_bottom_right - self.x_top_left

    @property
    def height(self) -> int:
        return self.y_bottom_right - self.y_top_left
