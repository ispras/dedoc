from dedoc.data_structures.annotation import Annotation


class SubscriptAnnotation(Annotation):
    """
    Subscript text inside the line.
    """
    name = "subscript"
    valid_values = ["True", "False"]

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the subscript text
        :param end: end of the subscript text (not included)
        :param value: True if subscript else False (False usually isn't used because you may not use this annotation at all)
        """
        try:
            bool(value)
        except ValueError:
            raise ValueError("the value of subscript annotation should be True or False")
        super().__init__(start=start, end=end, name=SubscriptAnnotation.name, value=value)
