from dedoc.data_structures.annotation import Annotation


class StrikeAnnotation(Annotation):
    """
    Strikethrough of some text inside the line.
    """
    name = "strike"
    valid_values = ["True", "False"]

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the strikethrough text
        :param end: end of the strikethrough text (not included)
        :param value: True if strikethrough else False (False usually isn't used because you may not use this annotation at all)
        """
        try:
            bool(value)
        except ValueError:
            raise ValueError("the value of strike annotation should be True or False")
        super().__init__(start=start, end=end, name=StrikeAnnotation.name, value=value)
