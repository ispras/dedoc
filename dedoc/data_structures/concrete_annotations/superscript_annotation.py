from dedoc.data_structures.annotation import Annotation


class SuperscriptAnnotation(Annotation):
    """
    Superscript text inside the line.
    """
    name = "superscript"
    valid_values = ["True", "False"]

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the superscript text
        :param end: end of the superscript text (not included)
        :param value: True if superscript else False (False usually isn't used because you may not use this annotation at all)
        """
        try:
            bool(value)
        except ValueError:
            raise ValueError("the value of superscript annotation should be True or False")
        super().__init__(start=start, end=end, name=SuperscriptAnnotation.name, value=value)
