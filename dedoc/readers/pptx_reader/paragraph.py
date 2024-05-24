from bs4 import Tag

from dedoc.data_structures import HierarchyLevel, LineMetadata, LineWithMeta
from dedoc.readers.pptx_reader.numbering_extractor import NumberingExtractor


class PptxParagraph:

    def __init__(self, xml: Tag, numbering_extractor: NumberingExtractor) -> None:
        self.xml = xml
        self.numbered_list_type = self.xml.buAutoNum.get("type", "arabicPeriod") if self.xml.buAutoNum else None
        self.level = int(self.xml.pPr.get("lvl", 0)) + 1
        self.numbering_extractor = numbering_extractor

    def get_line_with_meta(self, page_id: int, line_id: int, is_title: bool, shift: int = 0) -> LineWithMeta:
        """
        TODO
        - BoldAnnotation, ItalicAnnotation, UnderlinedAnnotation
        - SizeAnnotation
        - SuperscriptAnnotation, SubscriptAnnotation
        - Strike annotation
        - AlignmentAnnotation

        - numbered lists
        - headers (?)
        """
        text = ""
        hierarchy_level = HierarchyLevel.create_raw_text()

        if is_title:
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.header, level_1=1, level_2=self.level, can_be_multiline=False)
        elif self.numbered_list_type:  # numbered list
            text += self.numbering_extractor.get_text(self.numbered_list_type, shift)
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.list_item, level_1=2, level_2=self.level, can_be_multiline=False)
        elif self.xml.buChar:  # bullet list
            text += self.xml.buChar["char"] + " "
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.list_item, level_1=3, level_2=self.level, can_be_multiline=False)

        if self.xml.r:
            for run in self.xml.find_all("a:r"):
                for run_text in run:
                    if run_text.name == "t" and run.text:
                        text += run.text

        return LineWithMeta(f"{text}\n", metadata=LineMetadata(page_id=page_id, line_id=line_id, tag_hierarchy_level=hierarchy_level))
