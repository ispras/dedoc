from typing import List, Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_prefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bullet_prefix import BulletPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.letter_prefix import LetterPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class DefaultStructureExtractor(AbstractStructureExtractor):
    """
    This class corresponds the basic structure extraction from the documents.

    You can find the description of this type of structure in the section :ref:`other_structure`.
    """
    document_type = "other"

    prefix_list: List[LinePrefix] = [DottedPrefix, BracketPrefix, LetterPrefix, BulletPrefix]

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Extract basic structure from the given document and add additional information to the lines' metadata.
        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """
        previous_line = None

        for line in document.lines:
            if line.metadata.tag_hierarchy_level is None:
                line.metadata.tag_hierarchy_level = HierarchyLevel.create_unknown()

            if line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.unknown:
                line.metadata.hierarchy_level = self.get_list_hl_with_regexp(line, previous_line)
            else:
                line.metadata.hierarchy_level = self.__get_hl_with_tag(line)

            assert line.metadata.hierarchy_level is not None
            if line.metadata.hierarchy_level.line_type != HierarchyLevel.raw_text:
                previous_line = line

        return document

    def __get_hl_with_tag(self, line: LineWithMeta) -> HierarchyLevel:
        assert line.metadata.tag_hierarchy_level is not None
        level_1, level_2 = line.metadata.tag_hierarchy_level.level_1, line.metadata.tag_hierarchy_level.level_2

        if level_1 is None or level_2 is None:
            return line.metadata.tag_hierarchy_level

        if line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.header:
            return HierarchyLevel(level_1=1, level_2=level_2, can_be_multiline=False, line_type=HierarchyLevel.header)

        if line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.list_item:
            return HierarchyLevel(level_1=level_1, level_2=level_2, can_be_multiline=False, line_type=HierarchyLevel.list_item)

        return line.metadata.tag_hierarchy_level

    @staticmethod
    def get_list_hl_with_regexp(line: LineWithMeta, previous_line: Optional[LineWithMeta]) -> HierarchyLevel:
        prefix = get_prefix(DefaultStructureExtractor.prefix_list, line)

        # TODO dotted list without space after numbering, like "1.Some text"
        if prefix.name == DottedPrefix.name:  # list like 1.1.1
            depth = len(prefix.numbers)
            if all((n <= 1900 for n in prefix.numbers)) and depth <= 9:
                return HierarchyLevel(2, depth, False, line_type=HierarchyLevel.list_item)
            return HierarchyLevel.create_raw_text()

        if prefix.name == BracketPrefix.name:  # list like 1)
            # check if tesseract recognize russian б as 6 (bi as six)
            if prefix.prefix_num == 6 and previous_line is not None and previous_line.line.lower().strip().startswith(("a)", "а)")):
                return HierarchyLevel(4, 1, False, line_type=HierarchyLevel.list_item)  # here is russian and english letters
            return HierarchyLevel(3, 1, False, line_type=HierarchyLevel.list_item)

        if prefix.name == LetterPrefix.name:  # list like a)
            return HierarchyLevel(4, 1, False, line_type=HierarchyLevel.list_item)

        if prefix.name == BulletPrefix.name:  # bullet list
            return HierarchyLevel(5, 1, False, line_type=HierarchyLevel.list_item)  # TODO make bullet list

        # no match for any list has been found
        return HierarchyLevel(None, None, line.metadata.tag_hierarchy_level.can_be_multiline, HierarchyLevel.raw_text)
