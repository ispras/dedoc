from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class AlignmentAnnotation(Annotation):
    name = "alignment"

    def __init__(self, start: int, end: int, value: str):
        if value not in ["left", "right", "both", "center"]:
            raise ValueError("the value of alignment annotation should be left, right, both, or center")
        super().__init__(start=start, end=end, name=AlignmentAnnotation.name, value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('AlignmentAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='alignment of the text',
                                   required=True,
                                   example="left",
                                   enum=["left", "right", "both", "center"])
        })
