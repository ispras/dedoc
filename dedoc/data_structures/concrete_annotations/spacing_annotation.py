from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class SpacingAnnotation(Annotation):
    """
    This annotation contains spacing between the current line and the previous one.
    It's measured in twentieths of a point or one hundredths of a line according to the standard Office Open XML File Formats.
    """
    name = "spacing"

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        :param value: spacing between the current line and the previous one how it's defined in DOCX format (integer value)
        """
        try:
            int(value)
        except ValueError:
            raise ValueError("the value of spacing annotation should be a number, get {}".format(value))
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
