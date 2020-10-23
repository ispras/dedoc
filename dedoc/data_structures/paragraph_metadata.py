from collections import OrderedDict
from typing import Dict, Optional

from dedoc.data_structures.serializable import Serializable


class ParagraphMetadata(Serializable):
    """
    That class holds information about document node metadata, such as type or location
    :param paragraph_type: logical type of paragraph such as title or list_item
    :param predicted_classes: (optional), if the paragraph type was classified with some ml algorithm it can hold
    information about prediction probabilities.
    :param page_id: Page where paragraph starts. The numeration starts from page 0.
    :param line_id: Line number where paragraph starts.  The numeration starts from page 0.
    :param other_fields: additional fields of user metadata
    """

    def __init__(self, paragraph_type: str,
                    predicted_classes: Optional[Dict[str, float]],
                    page_id: int,
                    line_id: Optional[int],
                    other_fields=None):
        if other_fields is None:
            other_fields = {}
        if other_fields is None:
            other_fields = dict()
        self.paragraph_type = paragraph_type
        self.predicted_classes = predicted_classes
        self.page_id = page_id
        self.line_id = line_id
        self.other_fields = other_fields

    def extend_other_fields(self, new_fields: dict):
        assert(new_fields is not None)
        assert(len(new_fields) > 0)

        if self.other_fields is None:
            self.other_fields = {}
        for (key, value) in new_fields.items():
            self.other_fields[key] = value

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["paragraph_type"] = self.paragraph_type
        if self.predicted_classes is not None:
            res["predicted_classes"] = self.predicted_classes
        res["page_id"] = self.page_id
        res["line_id"] = self.line_id
        if self.other_fields is not None:
            for (key, value) in self.other_fields.items():
                res[key] = value

        return res
