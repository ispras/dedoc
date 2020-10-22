from typing import Optional, List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.paragraph_metadata import BaseParagraphMetadata
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


class LineWithMeta:

    def __init__(self,
                 line: str,
                 hierarchy_level: Optional[HierarchyLevel],
                 metadata: BaseParagraphMetadata,
                 annotations: List[Annotation]):
        """
        Structural unit of document - line (or paragraph) of text and its metadata. One LineWithMeta should not contain
        text from different logical parts of the document (for example document title and raw text of document should not
        lay in the same line) One the other one logical part of the document may be represented by more than one line
        (for example document title may consist of many lines).

        :param line: raw text of the document line
        :param hierarchy_level: special characteristic of line, helps to construct tree-structured representation from
        flat list of lines, define the nesting level of the line. The lower the level of the hierarchy,
        the closer it is to the root.
        :param metadata: line metadata (related to the entire line, as type of the line or page number)
        :param annotations: metadata refers to some part of the text, for example font size of font type and so on.
        """

        self.__check_hierarchy_level(hierarchy_level)
        self._line = line
        self._hierarchy_level = hierarchy_level
        assert isinstance(metadata, BaseParagraphMetadata)
        self._metadata = metadata
        self._annotations = annotations

    def __check_hierarchy_level(self, hierarchy_level: HierarchyLevel):
        if not (hierarchy_level is None or isinstance(hierarchy_level, HierarchyLevel)):
            raise Exception(hierarchy_level)
        assert hierarchy_level is None or hierarchy_level.level_1 is None or hierarchy_level.level_1 >= 0
        if not (hierarchy_level is None or hierarchy_level.level_2 is None or hierarchy_level.level_2 >= 0):
            raise Exception(hierarchy_level)

    @property
    def line(self) -> str:
        return self._line

    @property
    def hierarchy_level(self) -> HierarchyLevel:
        return self._hierarchy_level

    @property
    def metadata(self) -> BaseParagraphMetadata:
        return self._metadata

    @property
    def annotations(self) -> List[Annotation]:
        return self._annotations

    def set_hierarchy_level(self, hierarchy_level: Optional[HierarchyLevel]):
        self.__check_hierarchy_level(hierarchy_level)
        self._hierarchy_level = hierarchy_level

    def __repr__(self) -> str:
        return "LineWithMeta({})".format(self.line[:65])
