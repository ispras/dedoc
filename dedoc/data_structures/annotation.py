from collections import OrderedDict

from flask_restx import Api, Model, fields

from dedoc.data_structures.serializable import Serializable


class Annotation(Serializable):
    """
    Base class for text annotations of all kinds.
    Annotation is the piece of information about the text line: it's appearance or links to another document object.
    Look to the concrete kind of annotations to get mode examples.
    """

    def __init__(self, start: int, end: int, name: str, value: str) -> None:
        """
        Some kind of text information about symbols between start and end.
        For example Annotation(1, 13, "italic", "True") says that text between 1st and 13th symbol was writen in italic.

        :param start: start of the annotated text
        :param end: end of the annotated text (end isn't included)
        :param name: annotation's name
        :param value: information about annotated text
        """
        self.start = start
        self.end = end
        self.name = name
        self.value = value

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Annotation):
            return False
        return self.name == o.name and self.value == o.value and self.start == o.start and self.end == o.end

    def __str__(self) -> str:
        return "{name}({start}:{end}, {value})".format(name=self.name.capitalize(), start=self.start, end=self.end, value=self.value)

    def __repr__(self) -> str:
        return "{name}(...)".format(name=self.name.capitalize())

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["start"] = self.start
        res["end"] = self.end
        res["name"] = self.name
        res["value"] = self.value
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        names = ["style", "bold", "italic", "underlined", "size", "indentation", "alignment", "table",
                 "attachment", "spacing", "strike", "subscript", "superscript"]
        return api.model('Annotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'name': fields.String(description='annotation name', required=True, example='bold', enum=names),
            'value': fields.String(description='annotation value. For example, it may be font size value for size type '
                                               'or type of alignment for alignment type',
                                   required=True,
                                   example="left")
        })
