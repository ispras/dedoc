

from collections import OrderedDict
from typing import Dict, Optional

from flask_restx import fields, Api, Model

from dedoc.api.models.custom_fields import wild_any_fields, wild_forbid_fields
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
                 other_fields: Optional[dict] = None) -> None:
        self.paragraph_type = paragraph_type    # TODO deprecated in the future (when we insert all tags)
        self.predicted_classes = predicted_classes
        self.tag: Optional[str] = "unknown"     # TODO set of possible tags [list_item, header, link, page_id, footer, toc_item]
        # Tag can have level: hierarchy_level [level1, level2]:
        # list level1 > list_item level1
        # 1) фиксированные для всех документов: toc level1 > toc_item level1 > list level1 > list_item level1
        #                                       footer level1 > [link level1, page_id level1]
        # 2) динамичные, различаются от дока к доку: headers can have different levels (Header of document level1 > header of part level1)
        # So we present 'tag' like Tuple[str, HierarchyLevel]

        self.page_id = page_id
        self.line_id = line_id
        if other_fields is not None and len(other_fields) > 0:
            self.extend_other_fields(other_fields)
        self.__other_fields = {}

    def extend_other_fields(self, new_fields: dict) -> None:
        assert (new_fields is not None)
        assert (len(new_fields) > 0)

        for key, value in new_fields.items():
            setattr(self, key, value)
            self.__other_fields[key] = value

    def to_dict(self, old_version: bool) -> dict:
        res = OrderedDict()
        res["paragraph_type"] = self.paragraph_type
        if self.predicted_classes is not None:
            res["predicted_classes"] = self.predicted_classes
        res["page_id"] = self.page_id
        res["line_id"] = self.line_id
        res["other_fields"] = self.__other_fields
        for key, value in self.__other_fields.items():
            res[key] = value
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('ParagraphMetadata', {
            'paragraph_type': fields.String(description="paragraph type (header, list_item, list) and etc.",
                                            required=True,
                                            example="header"),
            'predicted_classes': fields.Nested(api.model("Predicts", {'*': wild_any_fields}),
                                               allow_null=True,
                                               skip_none=True,
                                               required=False,
                                               description="classification result, where [{type_paragraph: "
                                                           "probability}]. Probability is the probability that a "
                                                           "paragraph belongs to a specific paragraph type, "
                                                           "paragraph type values depends on the input document type"),
            'page_id': fields.Integer(description="page number of begin paragraph", required=False, example=0),
            'line_id': fields.Integer(description="line number of begin paragraph", required=True, example=13),
            '_*': wild_forbid_fields,  # don't get private fields
            '[a-z]*': wild_any_fields
        })
