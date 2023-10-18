from dedoc.data_structures.annotation import Annotation


class SizeAnnotation(Annotation):
    """
    This annotation contains the font size of some part of the line in points (1/72 of an inch).
    These units of measurement are taken from the standard Office Open XML File Formats.
    """
    name = "size"

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the annotated text
        :param end: end of the annotated text (not included)
        :param value: font size in points (1/72 of an inch) how it's defined in DOCX format
        """
        try:
            float(value)
        except ValueError:
            raise ValueError("the value of size annotation should be a number")
        super().__init__(start=start, end=end, name=SizeAnnotation.name, value=value)
