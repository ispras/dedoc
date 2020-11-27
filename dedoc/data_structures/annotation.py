from collections import OrderedDict

from flask_restplus import fields, Api, Model

from dedoc.data_structures.serializable import Serializable


class Annotation(Serializable):

    def __init__(self, start: int, end: int, name: str, value: str, other_fields: dict = None):
        """
        Some kind of text information about symbols between start and end.
        For example Annotation(1, 13, "italic", "True")
        says that text between 1st and 13st symbol was writen in italic
        If you need to add new annotation type, you should change check_annotation_correctness method

        :param start: annotated text start
        :param end: annotated text end
        :param name: annotation's name
        :param value: information about annotated text
        :param other_fields: additional fields of annotation
        """
        self.start = start
        self.end = end
        self.name = name
        self.value = value
        self.check_annotation_correctness(name, value)
        if other_fields is not None and len(other_fields) > 0:
            self.extend_other_fields(other_fields)

    def extend_other_fields(self, new_fields: dict):
        """
        Add new attributes for annotation if new_fields is not empty
        :param new_fields: additional fields of annotation
        """
        assert(new_fields is not None)
        assert(len(new_fields) > 0)
        for key, value in new_fields.items():
            setattr(self, key, value)

    def check_annotation_correctness(self, name: str, value: str):
        """
        Check if annotation with given name has correct value
        annotation with name "size" is measured in points (1/72 of an inch)
        annotation with name "indent" is measured in twentieths of a point (1/1440 of an inch)
        :param name: annotation's name
        :param value: annotation's value
        """
        available_names = ["style", "bold", "italic", "underlined", "size", "indentation", "alignment"]
        available_values = {
            "style": lambda x: True,
            "bold": lambda x: x in ["True", "False"],
            "italic": lambda x: x in ["True", "False"],
            "underlined": lambda x: x in ["True", "False"],
            "size": lambda x: self.__is_float(x),
            "indentation": lambda x: self.__is_float(x),
            "alignment": lambda x: x in ["left", "right", "both", "center"],
        }
        assert(name in available_names)
        assert(set(available_names) == set(available_values))
        assert(available_values[name](value))

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
            'value': fields.String(description='annotation value. For example, it may be font size value for size type'
                                               'or type of alignment for alignment type',
                                   required=True,
                                   example="left")
        })

    @staticmethod
    def __is_float(string):
        try:
            float(string)
            return True
        except ValueError:
            return False
