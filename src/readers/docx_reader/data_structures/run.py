from typing import Optional

from bs4 import BeautifulSoup

from src.readers.docx_reader.data_structures.base_props import BaseProperties
from src.readers.docx_reader.properties_extractor import change_caps


class Run(BaseProperties):

    def __init__(self,
                 properties: Optional[BaseProperties],
                 styles_extractor: "StylesExtractor"  # NOQA
                 ) -> None:
        """
        contains information about run properties
        :param properties: Paragraph or Run for copying it's properties
        :param styles_extractor: StylesExtractor
        """

        self.text = ""
        super().__init__(styles_extractor, properties)

    def get_text(self, xml: BeautifulSoup) -> None:
        """
        makes the text of run
        :param xml: BeautifulSoup tree with run properties
        """
        for tag in xml:
            if tag.name == 't' and tag.text:
                self.text += tag.text
            elif tag.name == 'tab':
                self.text += '\t'
            elif tag.name == 'br':
                self.text += '\n'
            elif tag.name == 'cr':
                self.text += '\r'
            elif tag.name == 'sym':
                try:
                    self.text += chr(int("0x" + tag['w:char'], 16))
                except KeyError:
                    pass
        change_caps(self, xml)
        if hasattr(self, "caps") and xml.caps:
            self.text = self.text.upper()

    def __repr__(self) -> str:
        return "Run({})".format(self.text[:30].replace("\n", r"\n"))

    def __eq__(self,
               other: "Run") -> bool:
        """
        :param other: Run
        """
        if not isinstance(other, Run):
            return False
        return (self.size == other.size and
                self.bold == other.bold and
                self.italic == other.italic and
                self.underlined == other.underlined and
                self.superscript == other.superscript and
                self.subscript == other.subscript)
