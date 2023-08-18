import abc
from typing import List, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures


class AbstractHierarchyLevelBuilder(abc.ABC):
    starting_line_types = [""]
    document_types = [""]
    """
    Class is extracted hierarchy level for each line of the input chunk.
    Where the chunk is list of LineWithMeta with their predicted labels from the classifier.
    The chunk is a block from the document.
    self.starting_line_type - is a predicted type of start line from classifier. It is a type of the first line of the chunk.
    You must set:
    1 - self.starting_line_type as the type of the first line of input chunk.
    2 - write function get_lines_with_hierarchy(...)
    """

    def can_build(self, tag: str, document_type: str) -> bool:
        """
        if the first line type of the chunk equals starting_line_type, then this is the right builder
        @param tag: the first line type of the input chunk
        @return: can or can't work with this builder
        """

        return tag in self.starting_line_types and document_type in self.document_types

    @abc.abstractmethod
    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        """
        is a major function for extraction hierarchy level
        for each LineWithMeta with label (predicted class from classifier)
        @param lines_with_labels - lines of input chunk (a block from document)
        """
        pass

    @staticmethod
    def _postprocess_roman(hierarchy_level: HierarchyLevel, line: LineWithMeta) -> LineWithMeta:
        if hierarchy_level.line_type == "subsection" and LawTextFeatures.roman_regexp.match(line.line):
            match = LawTextFeatures.roman_regexp.match(line.line)
            prefix = line.line[match.start(): match.end()]
            suffix = line.line[match.end():]
            symbols = [("T", "I"), ("Т", "I"), ("У", "V"), ("П", "II"), ("Ш", "III"), ("Г", "I")]
            for symbol_from, symbol_to in symbols:
                prefix = prefix.replace(symbol_from, symbol_to)
            line.set_line(prefix + suffix)
        return line
