from dedoc.data_structures.annotation import Annotation


class UnderlinedAnnotation(Annotation):
    """
    Underlined text inside the line.
    """
    name = "underlined"
    valid_values = ["True", "False"]

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the underlined text
        :param end: end of the underlined text (not included)
        :param value: True if underlined else False (False usually isn't used because you may not use this annotation at all)
        """
        try:
            bool(value)
        except ValueError:
            raise ValueError("the value of underlined annotation should be True or False")
        super().__init__(start=start, end=end, name=UnderlinedAnnotation.name, value=value)
