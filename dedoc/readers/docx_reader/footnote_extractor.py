from typing import Optional, List
import re

from bs4 import BeautifulSoup

from dedoc.readers.docx_reader.data_structures.base_props import BaseProperties
from dedoc.readers.docx_reader.data_structures.run import Run
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties


class FootnoteExtractor:

    def __init__(self, xml: BeautifulSoup, key: str = "footnote"):
        """
        :param xml: BeautifulSoup tree with styles
        :param key: footnote or endnote
        """
        self.id2footnote = {}
        if xml:
            for footnote in xml.find_all("w:{}".format(key)):
                footnote_id = footnote.get("w:id")
                footnote_text = "\n".join(t.text for t in footnote.find_all("w:t") if t.text)
                if footnote_id and footnote_text:
                    self.id2footnote[footnote_id] = footnote_text
