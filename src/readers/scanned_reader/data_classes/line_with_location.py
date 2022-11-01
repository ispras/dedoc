from typing import Optional, List

from src.data_structures.annotation import Annotation
from src.data_structures.line_with_meta import LineWithMeta
from src.data_structures.paragraph_metadata import ParagraphMetadata
from src.structure_parser.heirarchy_level import HierarchyLevel

from src.readers.scanned_reader.data_classes.tables.location import Location


class LineWithLocation(LineWithMeta):

    def __init__(self,
                 line: str,
                 hierarchy_level: Optional[HierarchyLevel],
                 metadata: ParagraphMetadata,
                 annotations: List[Annotation],
                 location: Location,
                 uid: str = None) -> None:
        self.location = location
        super().__init__(line, hierarchy_level, metadata, annotations, uid)

    def __repr__(self) -> str:
        text = self.line if len(self.line) < 65 else self.line[:62] + "..."
        return "LineWithLocation({})".format(text)

    def __str__(self) -> str:
        return self.__repr__()
