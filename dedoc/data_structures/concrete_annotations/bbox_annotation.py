import json

from dedoc.data_structures.annotation import Annotation
from flask_restx import fields, Api, Model

from dedoc.data_structures.bbox import BBox


class BBoxAnnotation(Annotation):
    """
    Coordinates of the line's bounding box (in pixels) - for pdf documents.
    """
    name = "bounding box"

    def __init__(self, start: int, end: int, value: BBox) -> None:
        """
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        :param value: bounding box where line is located
        """
        try:
            BBox(value.x_top_left, value.y_top_left, value.width, value.height)
        except ValueError:
            raise ValueError("the value of bounding box annotation should be instance of BBox")
        super().__init__(start=start, end=end, name=BBoxAnnotation.name, value=json.dumps(value.to_dict()))

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('BBoxAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='bounding box of text chunk',
                                   required=True,
                                   example='{"x_top_left": 0, "y_top_left": 0, "width": 70, "height": 20}')
        })
