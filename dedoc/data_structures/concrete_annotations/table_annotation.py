from dedoc.data_structures.annotation import Annotation


class TableAnnotation(Annotation):
    """
    This annotation indicate the place of the table in the original document.
    The line containing this annotation is placed directly before the referred table.
    """
    name = "table"

    def __init__(self, name: str, start: int, end: int) -> None:
        """
        :param name: unique identifier of the table which is referenced inside this annotation
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        """
        super().__init__(start=start, end=end, name=TableAnnotation.name, value=name, is_mergeable=False)
