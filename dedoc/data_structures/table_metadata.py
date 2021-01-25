from collections import OrderedDict
from typing import Optional
from flask_restx import fields, Api, Model

from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):

    def __init__(self, page_id: Optional[int], uid: str = ""):
        """
        Holds the information about the table location in the document
        :param page_id: number of page where table starts
        :uid: unique id of table
        """
        self.page_id = page_id
        self.uid = uid

    def to_dict(self, old_version: bool) -> dict:
        res = OrderedDict()
        res["page_id"] = self.page_id
        res["uid"] = self.uid
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('TableMetadata', {
            'page_id': fields.Integer(readonly=False, description='table start page number'),
            'uid': fields.String(description="table unique id")
        })
