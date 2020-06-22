from collections import OrderedDict


class DocumentMetadata:

    def __init__(self,
                 file_name: str,
                 size: int,
                 modified_time: int,
                 created_time: int,
                 access_time: int,
                 file_type: str):
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
