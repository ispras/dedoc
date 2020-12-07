from flask_restplus import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class StyleAnnotation(Annotation):
    def __init__(self, start: int, end: int, value: str):
        super().__init__(start=start, end=end, name="style", value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('StyleAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='style name',
                                   required=True,
                                   example="heading 1")
        })
