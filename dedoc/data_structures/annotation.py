from collections import OrderedDict
from flask_restx import Api, Model, fields

from dedoc.data_structures.serializable import Serializable


class Annotation(Serializable):

    def __init__(self, start: int, end: int, name: str, value: str):
        """
        Some kind of text information about symbols between start and end.
        For example Annotation(1, 13, "italic", "True")
        says that text between 1st and 13st symbol was writen in italic

        :param start: annotated text start
        :param end: annotated text end
        :param name: annotation's name
        :param value: information about annotated text
        """
        self.start = start
        self.end = end
        self.name = name
        self.value = value

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Annotation):
            return self.name == o.name and self.value == o.value and self.start == o.start and self.end == o.end
        return False

    def __str__(self) -> str:
        return "{name}({start}:{end}, {value})".format(name=self.name.capitalize(),
                                                       start=self.start,
                                                       end=self.end,
                                                       value=self.value)

    def __repr__(self) -> str:
        return "{name}(...)".format(name=self.name.capitalize())

    def to_dict(self, old_version: bool) -> dict:
        res = OrderedDict()
        res["start"] = self.start
        res["end"] = self.end
        if old_version:
            res["value"] = self.name + ":" + self.value
        else:
            res["name"] = self.name
            res["value"] = self.value
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        names = ["style", "bold", "italic", "underlined", "size", "indentation", "alignment", "table"]
        return api.model('Annotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'name': fields.String(description='annotation name', required=True, example='bold',
                                  enum=names),
            'value': fields.String(description='annotation value. For example, it may be font size value for size type '
                                               'or type of alignment for alignment type',
                                   required=True,
                                   example="left")
        })
