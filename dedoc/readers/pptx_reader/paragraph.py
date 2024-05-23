from bs4 import Tag

from dedoc.data_structures import HierarchyLevel, LineMetadata, LineWithMeta


class PptxParagraph:

    def __init__(self, xml: Tag) -> None:
        self.xml = xml

    def get_line_with_meta(self, page_id: int, line_id: int) -> LineWithMeta:
        """
        TODO
        - BoldAnnotation, ItalicAnnotation, UnderlinedAnnotation
        - SizeAnnotation
        - SuperscriptAnnotation, SubscriptAnnotation
        - AlignmentAnnotation

        - numbered lists
        - headers (?)
        """
        text = ""
        hierarchy_level = HierarchyLevel.create_raw_text()

        if self.xml.buChar:
            text += self.xml.buChar["char"] + " "
            level_2 = int(self.xml.pPr.get("lvl", 0)) + 1
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.list_item, level_1=3, level_2=level_2, can_be_multiline=False)

        if self.xml.r:
            for run in self.xml.find_all("a:r"):
                for run_text in run:
                    if run_text.name == "t" and run.text:
                        text += run.text

        return LineWithMeta(f"{text}\n", metadata=LineMetadata(page_id=page_id, line_id=line_id, tag_hierarchy_level=hierarchy_level))
