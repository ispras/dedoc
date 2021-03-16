from dedoc.data_structures.annotation import Annotation
from flask_restx import Model, Api, fields


class ImageAnnotation(Annotation):
    def __init__(self, name: str, start: int = -1, end: int = -1):
        super().__init__(start=start, end=end, name='image', value=name)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('ImageAnnotation', {
            'value': fields.String(description='ref to image', required=True, example="image fafffa145agh")
        })
