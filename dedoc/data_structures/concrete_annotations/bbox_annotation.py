import json

from flask_restx import Api, Model, fields

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.bbox import BBox


class BBoxAnnotation(Annotation):
    """
    Coordinates of the line's bounding box (in relative coordinates) - for pdf documents.
    """
    name = "bounding box"

    def __init__(self, start: int, end: int, value: BBox, page_width: int, page_height: int) -> None:
        """
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        :param value: bounding box where line is located
        :param page_width: width of original image with this bbox
        :param page_height: height of original image with this bbox
        """
        if not isinstance(value, BBox):
            raise ValueError("the value of bounding box annotation should be instance of BBox")

        super().__init__(start=start, end=end, name=BBoxAnnotation.name, value=json.dumps(value.to_relative_dict(page_width, page_height)))

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model("BBoxAnnotation", {
            "start": fields.Integer(description="annotation start index", required=True, example=0),
            "end": fields.Integer(description="annotation end index", required=True, example=4),
            "value": fields.String(description="bounding box of text chunk",
                                   required=True,
                                   example='{"x_top_left": 0, "y_top_left": 0, "width": 0.5, "height": 0.2, "page_width": 1000, "page_height": 400}')
        })
