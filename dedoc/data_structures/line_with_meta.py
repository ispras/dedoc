from typing import Optional, List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


class LineWithMeta:

    def __init__(self,
                 line: str,
                 hierarchy_level: Optional[HierarchyLevel],
                 metadata: ParagraphMetadata,
                 annotations: List[Annotation]):

        self.__check_hierarchy_level(hierarchy_level)
        self._line = line
        self._hierarchy_level = hierarchy_level
        assert isinstance(metadata, ParagraphMetadata)
        self._metadata = metadata
        self._annotations = annotations

    def __check_hierarchy_level(self, hierarchy_level: HierarchyLevel):
        assert hierarchy_level is None or isinstance(hierarchy_level, HierarchyLevel)
        assert hierarchy_level is None or hierarchy_level.level_1 is None or hierarchy_level.level_1 >= 0
        assert hierarchy_level is None or hierarchy_level.level_2 is None or hierarchy_level.level_2 >= 0

    @property
    def line(self) -> str:
        return self._line

    @property
    def hierarchy_level(self) -> HierarchyLevel:
        return self._hierarchy_level

    @property
    def metadata(self) -> ParagraphMetadata:
        return self._metadata

    @property
    def annotations(self) -> List[Annotation]:
        return self._annotations

    def set_hierarchy_level(self, hierarchy_level: Optional[HierarchyLevel]):
        self.__check_hierarchy_level(hierarchy_level)
        self._hierarchy_level = hierarchy_level

    def __repr__(self) -> str:
        return "LineWithMeta({})".format(self.line[:65])

    def add_metadata(self, param: dict):
        for key, value in param.items():
            self._metadata[key] = value



