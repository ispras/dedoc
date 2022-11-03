from flask_restx import Model, Api, fields

from dedoc.data_structures.annotation import Annotation


class TableAnnotation(Annotation):
    name = "table"

    def __init__(self, name: str, start: int, end: int) -> None:
        super().__init__(start=start, end=end, name=TableAnnotation.name, value=name)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('TableAnnotation', {
            'value': fields.String(description='ref to table', required=True, example="table fafffa145agh")
        })
