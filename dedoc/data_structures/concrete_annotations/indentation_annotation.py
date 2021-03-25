from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class IndentationAnnotation(Annotation):
    name = "indentation"

    def __init__(self, start: int, end: int, value: str):
        try:
            float(value)
        except ValueError:
            raise ValueError("the value of indentation annotation should be a number")
        super().__init__(start=start, end=end, name=IndentationAnnotation.name, value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('IndentationAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='text indentation in twentieths of a point (1/1440 of an inch)',
                                   required=True,
                                   example="720")
        })
