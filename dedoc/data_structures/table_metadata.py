from collections import OrderedDict
from typing import Optional

from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):

    def __init__(self, page_id: Optional[int]):
        """
        Holds the information about the table location in the document
        :param page_id: number of page where table starts
        """
        self.page_id = page_id

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["page_id"] = self.page_id
        return res
