import uuid
from collections import OrderedDict
from typing import Optional

from flask_restx import Api, Model, fields

from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):
    """
    This class holds the information about table unique identifier, rotation angle (if table has been rotated - for images) and so on.
    """
    def __init__(self, page_id: Optional[int], uid: Optional[str] = None, rotated_angle: float = 0.0) -> None:
        """
        :param page_id: number of the page where table starts
        :param uid: unique identifier of the table
        :param rotated_angle: value of the rotation angle by which the table was rotated during recognition
        """
        self.page_id = page_id
        self.uid = str(uuid.uuid4()) if not uid else uid
        self.rotated_angle = rotated_angle

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["uid"] = self.uid
        res["page_id"] = self.page_id
        res["rotated_angle"] = self.rotated_angle
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model("TableMetadata", {
            "page_id": fields.Integer(readonly=False, description="table start page number"),
            "uid": fields.String(description="table unique id"),
            "rotated_angle": fields.Float(readonly=False, description="At what angle should the table be rotated to use boxes")
        })
