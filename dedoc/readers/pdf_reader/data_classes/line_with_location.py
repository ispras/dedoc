from typing import List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.tables.location import Location


class LineWithLocation(LineWithMeta):

    def __init__(self, line: str, metadata: LineMetadata, annotations: List[Annotation], location: Location, uid: str = None, order: int = -1) -> None:
        self.location = location
        self.order = order
        super().__init__(line, metadata, annotations, uid)

    def __repr__(self) -> str:
        parent_repr = super().__repr__()
        return parent_repr.replace("LineWithMeta", "LineWithLocation")

    def __str__(self) -> str:
        return self.__repr__()
