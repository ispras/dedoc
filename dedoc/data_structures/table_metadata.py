from collections import OrderedDict
from typing import Optional


class TableMetadata:

    def __init__(self, page_id: Optional[int]):
        self.page_id = page_id

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["page_id"] = self.page_id
        return res
