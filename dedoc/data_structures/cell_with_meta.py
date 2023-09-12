from typing import List, Sized

from dedoc.data_structures import CellProperty
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.line_metadata import LineMetadata


class CellWithMeta(Sized):
    def __init__(self, lines: List[LineMetadata], cell_property: CellProperty) -> None:
        self.lines = lines
        self.cell_property = cell_property

    def get_annotations(self) -> List[Annotation]:
        pass

    def get_text(self) -> str:
        pass
