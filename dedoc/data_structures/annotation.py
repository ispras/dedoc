from dedoc.api.schema.annotation import Annotation as ApiAnnotation
from dedoc.data_structures.serializable import Serializable


class Annotation(Serializable):
    """
    Base class for text annotations of all kinds.
    Annotation is the piece of information about the text line: it's appearance or links to another document object.
    Look to the concrete kind of annotations to get mode examples.
    """

    def __init__(self, start: int, end: int, name: str, value: str, is_mergeable: bool = True) -> None:
        """
        Some kind of text information about symbols between start and end.
        For example Annotation(1, 13, "italic", "True") says that text between 1st and 13th symbol was writen in italic.

        :param start: start of the annotated text
        :param end: end of the annotated text (end isn't included)
        :param name: annotation's name
        :param value: information about annotated text
        :param is_mergeable: is it possible to merge annotations with the same value
        """
        self.start = start
        self.end = end
        self.name = name
        self.value = value
        self.is_mergeable = is_mergeable

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Annotation):
            return False
        return self.name == o.name and self.value == o.value and self.start == o.start and self.end == o.end

    def __str__(self) -> str:
        return f"{self.name.capitalize()}({self.start}:{self.end}, {self.value})"

    def __repr__(self) -> str:
        return f"{self.name.capitalize()}(...)"

    def to_api_schema(self) -> ApiAnnotation:
        return ApiAnnotation(start=self.start, end=self.end, name=self.name, value=self.value)
