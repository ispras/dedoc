from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class StrikeAnnotation(Annotation):
    name = "strike"
    valid_values = ["True", "False"]

    def __init__(self, start: int, end: int, value: str):
        try:
            bool(value)
        except ValueError:
            raise ValueError("the value of strike annotation should be True or False")
        super().__init__(start=start, end=end, name=StrikeAnnotation.name, value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('StrikeAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='indicator if the text is strikethrough or not',
                                   required=True,
                                   example="True",
                                   enum=StrikeAnnotation.valid_values)
        })
