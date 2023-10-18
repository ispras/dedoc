from dedoc.data_structures.annotation import Annotation


class StyleAnnotation(Annotation):
    """
    This annotation contains the information about style of the line in the document.
    For example, in docx documents lines can be highlighted using Heading styles.
    """
    name = "style"

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the annotated text
        :param end: end of the annotated text (not included)
        :param value: style name of the text procured from the document formatting if exist (e.g. Heading 1)
        """
        super().__init__(start=start, end=end, name=StyleAnnotation.name, value=value)
