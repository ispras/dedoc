from dedoc.data_structures.annotation import Annotation
from flask_restplus import Model, Api, fields


class TableAnnotation(Annotation):
    def __init__(self, name: str):
        super().__init__(start=-1, end=-1, name='table', value=name)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('TableAnnotation', {
            'name': fields.String(description='ref to table', required=True, example="table fafffa145agh"),
            'value': fields.String(description='ref to table', required=True, example="table fafffa145agh")
        })
