from collections import OrderedDict
from typing import List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta


class LineWithLabel(LineWithMeta):

    def __init__(self,
                 line: str,
                 metadata: LineMetadata,
                 annotations: List[Annotation],
                 label: str,
                 group: str,
                 uid: str = None) -> None:
        super().__init__(line=line, metadata=metadata, annotations=annotations, uid=uid)
        self.group = group
        self.label = label

    def to_dict(self) -> dict:
        result = OrderedDict()
        result["label"] = self.label
        result["line"] = self.line
        result["metadata"] = self.metadata.to_dict()
        result["annotations"] = [annotation.to_dict() for annotation in self.annotations]
        result["group"] = self.group
        result["uid"] = self.uid
        return result
