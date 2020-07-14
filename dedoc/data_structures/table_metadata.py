from collections import OrderedDict
from typing import Optional

from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):

    def __init__(self, page_id: Optional[int]):
        """
        Hold information about table location in document
        :param page_id: number of page where table starts
        """
        self.page_id = page_id

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["page_id"] = self.page_id
        return res
