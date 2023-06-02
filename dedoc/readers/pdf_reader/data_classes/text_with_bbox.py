from collections import OrderedDict
from typing import Optional, List
from uuid import uuid1

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.bbox import BBox


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
        if BBoxAnnotation.name not in [annotation.name for annotation in self.annotations]:
            self.annotations.append(BBoxAnnotation(start=0, end=len(text), value=bbox))
        self.uid = "bbox_{}".format(uuid1()) if uid is None else uid

    def __str__(self) -> str:
        return "TextWithBBox(bbox = {}, page = {}, text = {})".format(self.bbox, self.page_num, self.text)

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
