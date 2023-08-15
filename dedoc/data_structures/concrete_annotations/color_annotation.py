import json
from collections import OrderedDict

from dedoc.data_structures.annotation import Annotation


class ColorAnnotation(Annotation):
    """
    Color of some text inside the line in the RGB format.
    """
    name = "color_annotation"

    def __init__(self, start: int, end: int, red: float, green: float, blue: float) -> None:
        """
        :param start: start of the colored text
        :param end: end of the colored text (not included)
        :param red: mean value of the red color component in the pixels that are not white in the given bounding box
        :param green: mean value of the green color component in the pixels that are not white in the given bounding box
        :param blue: mean value of the blue color component in the pixels that are not white in the given bounding box
        """
        assert red >= 0
        assert green >= 0
        assert blue >= 0

        self.red = red
        self.blue = blue
        self.green = green

        value = OrderedDict()
        value["red"] = red
        value["blue"] = blue
        value["green"] = green
        super().__init__(start=start, end=end, name=ColorAnnotation.name, value=json.dumps(value))

    def __str__(self) -> str:
        return f"ColorAnnotation(red={self.red}, green={self.green}, blue={self.blue})"
