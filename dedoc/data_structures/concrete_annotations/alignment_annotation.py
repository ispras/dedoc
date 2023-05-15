from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class AlignmentAnnotation(Annotation):
    """
    This annotation defines the alignment of the entire line in the document: left, right, to the both sides of the page or in the center.
    """
    name = "alignment"
    valid_values = ["left", "right", "both", "center"]

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        :param value: kind of the line alignment: left, right, both of center
        """
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
                                   enum=AlignmentAnnotation.valid_values)
        })
