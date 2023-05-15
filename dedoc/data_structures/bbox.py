from collections import OrderedDict
from typing import Tuple, Dict

from dedoc.data_structures.serializable import Serializable


class BBox(Serializable):
    """
    Bounding box around some page object, the coordinate system starts from top left corner.
    """
    """

    0------------------------------------------------------------------------------------------------> x
    |                                   BBox
    |    (x_top_left, y_top_left)  o_____________________
    |                              |                    |
    |                              |     some text      |
    |                              |____________________o
    |                                                   (x_bottom_right, y_bottom_right)
    |
    |
    |
    |
    V y
    """
    def __init__(self, x_top_left: int, y_top_left: int, width: int, height: int) -> None:
        """
        The following parameters should have values of pixels number.

        :param x_top_left: x coordinate of the bbox top left corner
        :param y_top_left: y coordinate of the bbox top left corner
        :param width: bounding box width
        :param height: bounding box height
        """
        self.x_top_left = x_top_left
        self.y_top_left = y_top_left
        self.width = width
        self.height = height

    @property
    def x_bottom_right(self) -> int:
        return self.x_top_left + self.width

    @property
    def y_bottom_right(self) -> int:
        return self.y_top_left + self.height

    def __str__(self) -> str:
        return "BBox(x = {} y = {}, w = {}, h = {})".format(self.x_top_left, self.y_top_left, self.width, self.height)

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def square(self) -> int:
        """
        Square of the bbox.
        """
        return self.height * self.width

    @staticmethod
    def from_two_points(top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> "BBox":
        """
        Make the bounding box from two points.

        :param top_left: (x, y) point of the bbox top left corner
        :param bottom_right: (x, y) point of the bbox bottom right corner
        """
        x_top_left, y_top_left = top_left
        x_bottom_right, y_bottom_right = bottom_right
        return BBox(x_top_left=x_top_left,
                    y_top_left=y_top_left,
                    width=x_bottom_right - x_top_left,
                    height=y_bottom_right - y_top_left)

    def have_intersection_with_box(self, box: "BBox", threshold: float = 0.3) -> bool:
        """
        Check if the current bounding box has the intersection with another one.

        :param box: another bounding box to check intersection with
        :param threshold: the lowest value of the intersection over union used get boolean result
        """
        # determine the (x, y)-coordinates of the intersection rectangle
        xA = max(self.x_top_left, box.x_top_left)
        yA = max(self.y_top_left, box.y_top_left)
        xB = min(self.x_top_left + self.width, box.x_top_left + box.width)
        yB = min(self.y_top_left + self.height, box.y_top_left + box.height)
        # compute the area of intersection rectangle
        inter_a_area = max(0, xB - xA) * max(0, yB - yA)
        # compute the area of both the prediction and ground-truth
        # rectangles
        box_b_area = float(box.width * box.height)
        # compute the intersection over union by taking the intersection
        # area and dividing it by the sum of prediction + ground-truth
        # areas - the intersection area
        percent_intersection = inter_a_area / box_b_area if box_b_area > 0 else 0
        # return the intersection over union value
        return percent_intersection > threshold

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["x_top_left"] = self.x_top_left
        res["y_top_left"] = self.y_top_left
        res["width"] = self.width
        res["height"] = self.height
        return res

    @staticmethod
    def from_dict(some_dict: Dict[str, int]) -> "BBox":
        return BBox(**some_dict)
