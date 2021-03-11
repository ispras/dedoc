from dedoc.data_structures.annotation import Annotation
from flask_restx import Model, Api, fields


class AttachAnnotation(Annotation):
    """
    This annotation indicate the place of the attachment in the original document (for example the place where image
    was placed in the docx document)
    """

    def __init__(self, attach_uid: str, start: int = -1, end: int = -1):
        super().__init__(start=start, end=end, name='attachment', value=attach_uid)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('AttachAnnotation', {
            'value': fields.String(description='ref to table', required=True, example="table fafffa145agh")
        })
