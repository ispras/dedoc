from collections import OrderedDict
from typing import Optional

from flask_restplus import fields, Api, Model

from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):

    def __init__(self, page_id: Optional[int]):
        """
        Holds the information about the table location in the document
        :param page_id: number of page where table starts
        """
        self.page_id = page_id

    def to_dict(self, old_version: bool) -> dict:
        res = OrderedDict()
        res["page_id"] = self.page_id
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('TableMetadata', {
            'page_id': fields.Integer(readonly=False, description='table start page number')
        })
