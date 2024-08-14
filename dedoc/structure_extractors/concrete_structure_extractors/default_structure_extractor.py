from typing import List, Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class DefaultStructureExtractor(AbstractStructureExtractor):
    """
    This class corresponds the basic structure extraction from the documents.

    You can find the description of this type of structure in the section :ref:`other_structure`.
    """
    document_type = "other"

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Extract basic structure from the given document and add additional information to the lines' metadata.
        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """
        parameters = {} if parameters is None else parameters
        patterns = self.__get_patterns(parameters)

        for line in document.lines:
            line_pattern = None
            for pattern in patterns:
                if pattern.match(line):
                    line_pattern = pattern
                    break

            line.metadata.hierarchy_level = line_pattern.get_hierarchy_level(line) if line_pattern else HierarchyLevel.create_raw_text()
            assert line.metadata.hierarchy_level is not None

        return document

    def __get_patterns(self, parameters: dict) -> List[AbstractPattern]:
        if "patterns" not in parameters:
            from dedoc.structure_extractors.patterns.bracket_list_pattern import BracketListPattern
            from dedoc.structure_extractors.patterns.bullet_list_pattern import BulletListPattern
            from dedoc.structure_extractors.patterns.dotted_list_pattern import DottedListPattern
            from dedoc.structure_extractors.patterns.letter_list_pattern import LetterListPattern
            from dedoc.structure_extractors.patterns.tag_header_pattern import TagHeaderPattern
            from dedoc.structure_extractors.patterns.tag_list_pattern import TagListPattern
            from dedoc.structure_extractors.patterns.tag_pattern import TagPattern
            from dedoc.structure_extractors.patterns.tag_type_pattern import TagTypePattern

            patterns = [
                TagHeaderPattern(line_type=HierarchyLevel.header, level_1=1, can_be_multiline=False),
                TagListPattern(line_type=HierarchyLevel.list_item, level_1=2, can_be_multiline=False),
                DottedListPattern(line_type=HierarchyLevel.list_item, level_1=2, can_be_multiline=False),
                BracketListPattern(line_type=HierarchyLevel.list_item, level_1=3, level_2=1, can_be_multiline=False),
                LetterListPattern(line_type=HierarchyLevel.list_item, level_1=4, level_2=1, can_be_multiline=False),
                BulletListPattern(line_type=HierarchyLevel.list_item, level_1=5, level_2=1, can_be_multiline=False),
                TagTypePattern(),
                TagPattern(line_type=HierarchyLevel.raw_text)
            ]
        else:
            import json
            from dedoc.structure_extractors.patterns.utils import get_pattern

            patterns = parameters["patterns"]
            if isinstance(patterns, str):
                patterns = json.loads(patterns)
            assert isinstance(patterns, list)
            assert len(patterns) > 0
            if isinstance(patterns[0], dict):
                patterns = [get_pattern(pattern) for pattern in patterns]

        assert isinstance(patterns[0], AbstractPattern)
        return patterns
