import uuid
from collections import OrderedDict

from flask_restx import fields, Api, Model

from dedoc.api.models.custom_fields import wild_any_fields
from dedoc.data_structures.serializable import Serializable


class DocumentMetadata(Serializable):
    """
    This class holds information about document metadata.
    """

    def __init__(self,
                 file_name: str,
                 size: int,
                 modified_time: int,
                 created_time: int,
                 access_time: int,
                 file_type: str,
                 other_fields: dict = None,
                 uid: str = None) -> None:
        """
        :param uid: document unique identifier (useful for attached files)
        :param file_name: original document name (before rename and conversion, so it can contain non-ascii symbols, spaces and so on)
        :param size: size of the original file in bytes
        :param modified_time: time of the last modification in unix time format (seconds since the epoch)
        :param created_time: time of the creation in unixtime
        :param access_time: time of the last access to the file in unixtime
        :param file_type: mime type of the file
        :param other_fields: additional fields of user metadata
        """
        self.file_name = file_name
        self.size = size
        self.modified_time = modified_time
        self.created_time = created_time
        self.access_time = access_time
        self.file_type = file_type
        self.other_fields = {}
        if other_fields is not None and len(other_fields) > 0:
            self.extend_other_fields(other_fields)
        self.uid = "doc_uid_auto_{}".format(uuid.uuid1()) if uid is None else uid

    def set_uid(self, uid: str) -> None:
        self.uid = uid  # noqa

    def extend_other_fields(self, new_fields: dict) -> None:
        """
        Add new attributes to the class and to the other_fields dictionary.

        :param new_fields: fields to add
        """
        assert (new_fields is not None)
        assert (len(new_fields) > 0)

        for key, value in new_fields.items():
            setattr(self, key, value)
            self.other_fields[key] = value

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["uid"] = self.uid
        res["file_name"] = self.file_name
        res["size"] = self.size
        res["modified_time"] = self.modified_time
        res["created_time"] = self.created_time
        res["access_time"] = self.access_time
        res["file_type"] = self.file_type
        if self.other_fields is not None:
            for (key, value) in self.other_fields.items():
                res[key] = value
        res["other_fields"] = self.other_fields
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('DocumentMetadata', {
            "uid": fields.String(description='unique document identifier', example="doc_uid_auto_ba73d76a-326a-11ec-8092-417272234cb0"),
            'file_name': fields.String(description='file name', example="example.odt"),
            'size': fields.Integer(description='file size in bytes', example="20060"),
            'modified_time': fields.Integer(description='modification time of the document in the format UnixTime', example="1590579805"),
            'created_time': fields.Integer(description='creation time of the document in the format UnixTime', example="1590579805"),
            'access_time': fields.Integer(description='file access time in format UnixTime', example="1590579805"),
            'file_type': fields.String(description='mime-type file', example="application/vnd.oasis.opendocument.text"),
            '[a-z]*': wild_any_fields
        })
