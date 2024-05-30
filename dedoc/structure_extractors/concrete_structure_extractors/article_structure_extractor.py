from typing import List, Optional

from dedoc.data_structures import HierarchyLevel, UnstructuredDocument
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors import AbstractStructureExtractor


class ArticleStructureExtractor(AbstractStructureExtractor):
    """
    This class corresponds to the `GROBID <https://grobid.readthedocs.io/en/latest/>`_ article structure extraction.

    This class saves all tag_hierarchy_levels received from the :class:`~dedoc.readers.ArticleReader` \
    without using the postprocessing step (without using regular expressions).

    You can find the description of this type of structure in the section :ref:`article_structure`.
    """
    document_type = "article"

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Extract article structure from the given document and add additional information to the lines' metadata.
        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """
        for line in document.lines:
            if line.metadata.tag_hierarchy_level is None or line.metadata.tag_hierarchy_level.is_unknown():
                line.metadata.tag_hierarchy_level = HierarchyLevel.create_raw_text()
            else:
                line.metadata.hierarchy_level = line.metadata.tag_hierarchy_level
            assert line.metadata.hierarchy_level is not None

        return document

    def _postprocess(self, lines: List[LineWithMeta], paragraph_type: List[str], regexps: List, excluding_regexps: List) -> List[LineWithMeta]:
        return lines
