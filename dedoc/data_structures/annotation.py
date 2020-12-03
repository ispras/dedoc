from collections import OrderedDict
from flask_restplus import Api, Model, fields

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

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["start"] = self.start
        res["end"] = self.end
        res["name"] = self.name
        res["value"] = self.value
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('Annotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'name': fields.String(description='annotation name', required=True, example='bold',
                                  enum=["style", "bold", "italic", "underlined", "size", "indentation", "alignment"]),
            'value': fields.String(description='annotation value. For example, it may be font size value for size type '
                                               'or type of alignment for alignment type',
                                   required=True,
                                   example="left")
        })


