from collections import OrderedDict

from dedoc.data_structures.serializable import Serializable


class DocumentMetadata(Serializable):
    """
        holds information about document metadata.
        :param file_name: original document name (before rename and conversion, so it can contain non-ascii symbols,
        spaces and so on)
        :param size: size of the original file in bytes
        :param modified_time: time of the last modification in unix time format (seconds since the epoch)
        :param created_time: time of the creation in unixtime
        :param access_time: time of the last acess to the file in unixtime
        :param file_type: mime type of the file
        :param other_fields: additional fields of user metadata
    """

    def __init__(self,
                    file_name: str,
                    size: int,
                    modified_time: int,
                    created_time: int,
                    access_time: int,
                    file_type: str,
                    other_fields: dict = None):
        self.file_name = file_name
        self.size = size
        self.modified_time = modified_time
        self.created_time = created_time
        self.access_time = access_time
        self.file_type = file_type
        self.other_fields = other_fields

    def extend_other_fields(self, new_fields: dict):
        assert (new_fields is not None)
        assert (len(new_fields) > 0)

        if self.other_fields is None:
            self.other_fields = {}
        for (key, value) in new_fields.items():
            self.other_fields[key] = value

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["file_name"] = self.file_name
        res["size"] = self.size
        res["modified_time"] = self.modified_time
        res["created_time"] = self.created_time
        res["access_time"] = self.access_time
        res["file_type"] = self.file_type
        if self.other_fields is not None:
            for (key, value) in self.other_fields.items():
                res[key] = value

        return res
