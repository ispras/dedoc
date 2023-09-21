import uuid
from collections import OrderedDict
from typing import Optional

from flask_restx import Api, Model, fields

from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):
    """
    This class holds the information about the table location in the document and information about cell properties.
    """
    def __init__(self, page_id: Optional[int], uid: Optional[str] = None, is_inserted: bool = False) -> None:
        """
        :param page_id: number of the page where table starts
        :param uid: unique identifier of the table
        :param is_inserted: indicator if table was already inserted into paragraphs list
        :param cell_properties: information about rowspan, colspan and invisibility of each cell
        """
        self.page_id = page_id
        self.uid = str(uuid.uuid1()) if not uid else uid
        self.is_inserted = is_inserted

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["uid"] = self.uid
        res["page_id"] = self.page_id
        res["is_inserted"] = self.is_inserted
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model("TableMetadata", {
            "page_id": fields.Integer(readonly=False, description="table start page number"),
            "uid": fields.String(description="table unique id"),
            "is_inserted": fields.Boolean(description="was the table inserted into document body")
        })
