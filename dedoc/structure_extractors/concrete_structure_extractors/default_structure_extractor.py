from typing import Optional

from dedoc.common.exceptions.structure_extractor_error import StructureExtractorError
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern
from dedoc.structure_extractors.patterns.pattern_composition import PatternComposition


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

        ``parameters`` parameter can contain patterns for configuring lines types and their levels in the output document tree ("patterns" key).
        Please see :ref:`dedoc_structure_extractors_patterns` and :ref:`using_patterns` to get information how to use patterns for making your custom structure.
        """
        parameters = {} if parameters is None else parameters
        pattern_composition = self.__get_pattern_composition(parameters)

        for line in document.lines:
            line.metadata.hierarchy_level = pattern_composition.get_hierarchy_level(line=line)
        return document

    def __get_pattern_composition(self, parameters: dict) -> PatternComposition:
        patterns = parameters.get("patterns")
        if not patterns:
            from dedoc.structure_extractors.patterns.bracket_list_pattern import BracketListPattern
            from dedoc.structure_extractors.patterns.bullet_list_pattern import BulletListPattern
            from dedoc.structure_extractors.patterns.dotted_list_pattern import DottedListPattern
            from dedoc.structure_extractors.patterns.letter_list_pattern import LetterListPattern
            from dedoc.structure_extractors.patterns.roman_list_pattern import RomanListPattern
            from dedoc.structure_extractors.patterns.tag_header_pattern import TagHeaderPattern
            from dedoc.structure_extractors.patterns.tag_list_pattern import TagListPattern
            from dedoc.structure_extractors.patterns.tag_pattern import TagPattern

            return PatternComposition(
                patterns=[
                    TagHeaderPattern(line_type=HierarchyLevel.header, level_1=1, can_be_multiline=False),
                    TagListPattern(line_type=HierarchyLevel.list_item, default_level_1=2, can_be_multiline=False),
                    DottedListPattern(line_type=HierarchyLevel.list_item, level_1=2, can_be_multiline=False),
                    RomanListPattern(line_type=HierarchyLevel.list_item, level_1=3, level_2=1, can_be_multiline=False),
                    BracketListPattern(line_type=HierarchyLevel.list_item, level_1=4, level_2=1, can_be_multiline=False),
                    LetterListPattern(line_type=HierarchyLevel.list_item, level_1=5, level_2=1, can_be_multiline=False),
                    BulletListPattern(line_type=HierarchyLevel.list_item, level_1=6, level_2=1, can_be_multiline=False),
                    TagPattern(default_line_type=HierarchyLevel.raw_text)
                ]
            )

        import ast
        from dedoc.structure_extractors.patterns.utils import get_pattern

        if isinstance(patterns, str):
            try:
                patterns = ast.literal_eval(patterns)
            except ValueError as e:
                raise StructureExtractorError(msg=f"Bad syntax for patterns: {str(e)}")

        if not isinstance(patterns, list):
            raise StructureExtractorError(msg="Patterns parameter should contain a list of patterns")

        pattern_classes = []
        for pattern in patterns:
            if isinstance(pattern, dict):
                pattern_classes.append(get_pattern(pattern))
            elif isinstance(pattern, AbstractPattern):
                pattern_classes.append(pattern)
            else:
                raise StructureExtractorError(msg="Pattern should be dict or `AbstractPattern`")

        return PatternComposition(patterns=pattern_classes)
