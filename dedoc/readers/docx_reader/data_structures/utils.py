import hashlib
import logging
import time
from typing import List

from bs4 import Tag

from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.readers.docx_reader.footnote_extractor import FootnoteExtractor
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor


class Counter:

    def __init__(self, body: Tag, logger: logging.Logger) -> None:
        self.logger = logger
        self.total_paragraph_number = sum([len(p.find_all("w:p")) for p in body if p.name != "p" and p.name != "tbl" and isinstance(p, Tag)])
        self.total_paragraph_number += len([p for p in body if p.name == "p" and isinstance(p, Tag)])
        self.current_paragraph_number = 0
        self.checkpoint_time = time.time()

    def inc(self) -> None:
        self.current_paragraph_number += 1
        current_time = time.time()
        if current_time - self.checkpoint_time > 3:
            self.logger.info(f"Processed {self.current_paragraph_number} paragraphs from {self.total_paragraph_number}")
            self.checkpoint_time = current_time


class ParagraphMaker:

    def __init__(self,
                 path_hash: str,
                 counter: Counter,
                 styles_extractor: StylesExtractor,
                 numbering_extractor: NumberingExtractor,
                 footnote_extractor: FootnoteExtractor,
                 endnote_extractor: FootnoteExtractor) -> None:
        self.counter = counter
        self.path_hash = path_hash
        self.styles_extractor = styles_extractor
        self.numbering_extractor = numbering_extractor
        self.footnote_extractor = footnote_extractor
        self.endnote_extractor = endnote_extractor
        self.uids_set = set()

    def make_paragraph(self, paragraph_xml: Tag, paragraph_list: List[Paragraph]) -> Paragraph:
        uid = self.__get_paragraph_uid(paragraph_xml=paragraph_xml)
        paragraph = Paragraph(xml=paragraph_xml,
                              styles_extractor=self.styles_extractor,
                              numbering_extractor=self.numbering_extractor,
                              footnote_extractor=self.footnote_extractor,
                              endnote_extractor=self.endnote_extractor,
                              uid=uid)
        prev_paragraph = None if len(paragraph_list) == 0 else paragraph_list[-1]
        paragraph.spacing = paragraph.spacing_before if prev_paragraph is None else max(prev_paragraph.spacing_after, paragraph.spacing_before)
        self.counter.inc()
        return paragraph

    def __get_paragraph_uid(self, paragraph_xml: Tag) -> str:
        xml_hash = hashlib.md5(paragraph_xml.encode()).hexdigest()
        raw_uid = f"{self.path_hash}_{xml_hash}"
        uid = raw_uid
        n = 0
        while uid in self.uids_set:
            n += 1
            uid = f"{raw_uid}_{n}"
        self.uids_set.add(uid)
        return uid
