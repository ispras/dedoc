from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class IndentationAnnotation(Annotation):
    """
    This annotation contains the indentation of the entire line in twentieths of a point (1/1440 of an inch).
    These units of measurement are taken from the standard Office Open XML File Formats.
    """
    name = "indentation"

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        :param value: text indentation in twentieths of a point (1/1440 of an inch) how it's defined in DOCX format
        """
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
