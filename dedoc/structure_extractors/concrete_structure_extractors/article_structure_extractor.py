from typing import List, Optional

from dedoc.data_structures import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors import DefaultStructureExtractor


class ArticleStructureExtractor(DefaultStructureExtractor):
    """
    This class corresponds the GROBID article structure extraction.
    This class saves all tag_hierarchy_levels received from ArticleReader:

    * without using postprocessing step (without using regexp)

    * without analyse unknown tag (without using regexp, without get_hl_list_using_regexp)

    Here we save a GROBID structure using method ``extract`` of class :class:`~dedoc.structure_extractors.DefaultStructureExtractor`.
    """
    document_type = "article"

    def _postprocess(self, lines: List[LineWithMeta], paragraph_type: List[str], regexps: List, excluding_regexps: List) -> List[LineWithMeta]:
        return lines

    @staticmethod
    def get_hl_list_using_regexp(line: LineWithMeta, previous_line: Optional[LineWithMeta]) -> HierarchyLevel:
        return HierarchyLevel(None, None, line.metadata.tag_hierarchy_level.can_be_multiline, HierarchyLevel.raw_text)
