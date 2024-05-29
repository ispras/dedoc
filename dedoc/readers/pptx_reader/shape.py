from collections import defaultdict
from typing import List

from bs4 import Tag

from dedoc.data_structures import LineWithMeta
from dedoc.readers.pptx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.pptx_reader.paragraph import PptxParagraph
from dedoc.readers.pptx_reader.properties_extractor import PropertiesExtractor


class PptxShape:
    """
    This class corresponds to one textual block of the presentation (tag <a:sp>).
    """
    def __init__(self, xml: Tag, page_id: int, init_line_id: int, numbering_extractor: NumberingExtractor, properties_extractor: PropertiesExtractor,
                 is_title: bool = False) -> None:
        self.xml = xml
        self.page_id = page_id
        self.init_line_id = init_line_id
        self.numbering_extractor = numbering_extractor
        self.properties_extractor = properties_extractor
        self.is_title = is_title

    def get_lines(self) -> List[LineWithMeta]:
        if not self.xml.get_text().strip():
            return []

        if self.xml.ph and "title" in self.xml.ph.get("type", "").lower():
            self.is_title = True

        lines = []
        numbering2shift = defaultdict(int)
        prev_list_level = None

        for line_id, paragraph_xml in enumerate(self.xml.find_all("a:p")):
            paragraph = PptxParagraph(paragraph_xml, self.numbering_extractor, self.properties_extractor)

            if paragraph.numbered_list_type:
                if prev_list_level and paragraph.level > prev_list_level:
                    numbering2shift[(paragraph.numbered_list_type, paragraph.level)] = 0

                shift = numbering2shift[(paragraph.numbered_list_type, paragraph.level)]
                numbering2shift[(paragraph.numbered_list_type, paragraph.level)] += 1
                prev_list_level = paragraph.level
            else:
                shift = 0

            lines.append(paragraph.get_line_with_meta(line_id=self.init_line_id + line_id, page_id=self.page_id, is_title=self.is_title, shift=shift))

        return lines
