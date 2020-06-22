from collections import OrderedDict
from typing import Dict, Optional


class ParagraphMetadata:

    def __init__(self,
                 paragraph_type: str,
                 predicted_classes: Optional[Dict[str, float]],
                 page_id: int,
                 line_id: Optional[int]):
        self.paragraph_type = paragraph_type
        self.predicted_classes = predicted_classes
        self.page_id = page_id
        self.line_id = line_id

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["paragraph_type"] = self.paragraph_type
        if self.predicted_classes is not None:
            res["predicted_classes"] = self.predicted_classes
        res["page_id"] = self.page_id
        res["line_id"] = self.line_id
        return res
