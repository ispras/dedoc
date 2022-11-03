import json
from collections import OrderedDict

from dedoc.data_structures.annotation import Annotation


class ColorAnnotation(Annotation):

    name = "color_annotation"

    def __init__(self, start: int, end: int, red: float, green: float, blue: float) -> None:
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
        return "ColorAnnotation(red={}, green={}, blue={})".format(self.red, self.green, self.blue)
