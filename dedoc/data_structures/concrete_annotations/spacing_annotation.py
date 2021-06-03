from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class SpacingAnnotation(Annotation):
    name = "spacing"

    def __init__(self, start: int, end: int, value: str):
        try:
            int(value)
        except ValueError:
            raise ValueError("the value of spacing annotation should be a number")
        super().__init__(start=start, end=end, name=SpacingAnnotation.name, value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('SpacingAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='spacing between the current line and the previous one in '
                                               'twentieths of a point or one hundredths of a line',
                                   required=True,
                                   example="240")
        })
