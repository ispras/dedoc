from dedoc.data_structures.annotation import Annotation
from flask_restx import Model, Api, fields


class TableAnnotation(Annotation):
    def __init__(self, name: str, start: int = -1, end: int = -1):
        super().__init__(start=start, end=end, name='table', value=name)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('TableAnnotation', {
            'value': fields.String(description='ref to table', required=True, example="table fafffa145agh")
        })
