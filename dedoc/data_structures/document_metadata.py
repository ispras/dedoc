from collections import OrderedDict

from dedoc.data_structures.serializable import Serializable


class DocumentMetadata(Serializable):

    def __init__(self,
                 file_name: str,
                 size: int,
                 modified_time: int,
                 created_time: int,
                 access_time: int,
                 file_type: str):
        """
        hold information about document metadata.
        :param file_name: original document name (before rename and conversion, so it may contain non-ascii,
        spaces and so on)
        :param size: size of the original file in bytes
        :param modified_time: time of the last modification in unix time format (seconds since the epoch)
        :param created_time: time of the creation in unixtime
        :param access_time: time of the last acess to the file in unixtime
        :param file_type: mime type of the file
        """
        self.file_name = file_name
        self.size = size
        self.modified_time = modified_time
        self.created_time = created_time
        self.access_time = access_time
        self.file_type = file_type

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["file_name"] = self.file_name
        res["size"] = self.size
        res["modified_time"] = self.modified_time
        res["created_time"] = self.created_time
        res["access_time"] = self.access_time
        res["file_type"] = self.file_type
        return res
