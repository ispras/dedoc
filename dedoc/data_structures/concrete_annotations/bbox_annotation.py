
import json

from dedoc.data_structures.annotation import Annotation
from flask_restx import fields, Api, Model

from dedoc.readers.scanned_reader.data_classes.bbox import BBox


class BBoxAnnotation(Annotation):

    name = "bounding box"

    def __init__(self, start: int, end: int, value: BBox) -> None:
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
                                   example="True")
        })
