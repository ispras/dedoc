from collections import defaultdict
from typing import List

from bs4 import Tag

from dedoc.data_structures import LineWithMeta
from dedoc.readers.pptx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.pptx_reader.paragraph import PptxParagraph
from dedoc.readers.pptx_reader.properties_extractor import PropertiesExtractor


class PptxShape:
    def __init__(self, xml: Tag, page_id: int, init_line_id: int, numbering_extractor: NumberingExtractor, properties_extractor: PropertiesExtractor) -> None:
        self.xml = xml
        self.page_id = page_id
        self.init_line_id = init_line_id
        self.numbering_extractor = numbering_extractor
        self.properties_extractor = properties_extractor
        self.is_title = False

    def get_lines(self) -> List[LineWithMeta]:
        if self.xml.ph and "title" in self.xml.ph.get("type", "").lower():
            self.is_title = True

        lines = []
        numbering2shift = defaultdict(int)

        for line_id, paragraph_xml in enumerate(self.xml.find_all("a:p")):
            paragraph = PptxParagraph(paragraph_xml, self.numbering_extractor, self.properties_extractor)

            if paragraph.numbered_list_type:
                shift = numbering2shift[(paragraph.numbered_list_type, paragraph.level)]
                numbering2shift[(paragraph.numbered_list_type, paragraph.level)] += 1
            else:
                shift = 0

            lines.append(paragraph.get_line_with_meta(line_id=self.init_line_id + line_id, page_id=self.page_id, is_title=self.is_title, shift=shift))

        return lines