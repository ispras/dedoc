from collections import OrderedDict
from typing import List, Optional
from uuid import uuid1

from dedocutils.data_structures import BBox

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.serializable import Serializable


class TextWithBBox(Serializable):

    def __init__(self,
                 bbox: BBox,
                 page_num: int,
                 text: str,
                 line_num: int,
                 uid: Optional[str] = None,
                 label: Optional[str] = None,
                 annotations: List[Annotation] = None) -> None:
        self.bbox = bbox
        self.page_num = page_num
        self.line_num = line_num
        self.text = text
        self.label = label
        self.annotations = [] if annotations is None else annotations
        self.uid = f"bbox_{uuid1()}" if uid is None else uid

    def __str__(self) -> str:
        return f"TextWithBBox(bbox = {self.bbox}, page = {self.page_num}, text = {self.text})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["uid"] = self.uid
        res["_uid"] = self.uid
        res["bbox"] = self.bbox.to_dict()
        res["page_num"] = self.page_num
        res["line_num"] = self.line_num
        res["text"] = self.text
        res["label"] = self.label
        return res
