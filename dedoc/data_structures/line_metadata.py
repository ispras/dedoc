from collections import OrderedDict
from typing import Optional

from flask_restx import fields, Api, Model

from dedoc.api.models.custom_fields import wild_any_fields, wild_forbid_fields
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.serializable import Serializable


class LineMetadata(Serializable):
    """
    This class holds information about document node (and document line) metadata, such as page number or line level in a document hierarchy.
    """

    def __init__(self,
                 page_id: int,
                 line_id: Optional[int],
                 tag_hierarchy_level: Optional[HierarchyLevel] = None,
                 hierarchy_level: Optional[HierarchyLevel] = None,
                 other_fields: Optional[dict] = None) -> None:
        """
        :param page_id: page number where paragraph starts, the numeration starts from page 0
        :param line_id: line number inside the entire document, the numeration starts from line 0
        :param tag_hierarchy_level: the hierarchy level of the line with its type directly extracted by some of the readers
            (usually information got from tags e.g. in docx or html readers)
        :param hierarchy_level: the hierarchy level of the line extracted by some of the structure extractors - the result type and level of the line.
            The lower the level of the hierarchy, the closer it is to the root, it's used to construct document tree.
        :param other_fields: additional fields of user metadata
        """
        self.tag_hierarchy_level = HierarchyLevel(None, None, can_be_multiline=True, line_type=HierarchyLevel.unknown) \
            if tag_hierarchy_level is None else tag_hierarchy_level
        self.hierarchy_level = hierarchy_level
        self.page_id = page_id
        self.line_id = line_id
        if other_fields is not None and len(other_fields) > 0:
            self.extend_other_fields(other_fields)
        self.__other_fields = {}

    def extend_other_fields(self, new_fields: dict) -> None:
        """
        Add new attributes to the class and to the other_fields dictionary.

        :param new_fields: fields to add
        """
        assert (new_fields is not None)
        assert (len(new_fields) > 0)

        for key, value in new_fields.items():
            setattr(self, key, value)
            self.__other_fields[key] = value

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["page_id"] = self.page_id
        res["line_id"] = self.line_id
        res["paragraph_type"] = self.hierarchy_level.line_type if self.hierarchy_level is not None else HierarchyLevel.raw_text
        res["other_fields"] = self.__other_fields
        for key, value in self.__other_fields.items():
            res[key] = value
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('LineMetadata', {
            'paragraph_type': fields.String(description="paragraph type (header, list_item, list) and etc.", required=True, example="header"),
            'page_id': fields.Integer(description="page number of begin paragraph", required=False, example=0),
            'line_id': fields.Integer(description="line number of begin paragraph", required=True, example=13),
            '_*': wild_forbid_fields,  # don't get private fields
            'tag_hierarchy_level': wild_forbid_fields,
            'hierarchy_level': wild_forbid_fields,
            '[a-z]*': wild_any_fields
        })
