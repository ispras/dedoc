from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class LinkedTextAnnotation(Annotation):
    """
    This annotation is used when some text is linked to the line or its part.
    For example, line can contain a number that refers the footnote - the text of this footnote will be the value of this annotation.
    """
    name = "linked_text"

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the annotated text
        :param end: end of the annotated text (not included)
        :param value: text, linked to given one, for example text of the footnote
        """
        super().__init__(start=start, end=end, name=LinkedTextAnnotation.name, value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('LinkedTextAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='text, linked to given, for example text of the footnote',
                                   required=True,)
        })
