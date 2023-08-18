from typing import Optional

from bs4 import Tag

from dedoc.readers.docx_reader.data_structures.base_props import BaseProperties
from dedoc.readers.docx_reader.properties_extractor import change_caps


class Run(BaseProperties):

    def __init__(self, properties: Optional[BaseProperties], styles_extractor: "StylesExtractor") -> None:  # noqa
        """
        Contains information about run properties.
        :param properties: Paragraph or Run for copying its properties
        :param styles_extractor: StylesExtractor
        """

        self.name2char = dict(tab="\t", br="\n", cr="\r")
        self.text = ""
        self.styles_extractor = styles_extractor
        super().__init__(properties)

    def get_text(self, xml: Tag) -> None:
        """
        Makes the text of run.
        :param xml: BeautifulSoup tree with run properties
        """
        for tag in xml:
            tag_name = tag.name

            if tag_name in self.name2char:
                self.text += self.name2char[tag_name]
                continue

            if tag_name == "t" and tag.text:
                self.text += tag.text

            elif tag_name == "sym":
                try:
                    self.text += chr(int("0x" + tag["w:char"], 16))
                except KeyError:
                    pass

        change_caps(self, xml)
        if hasattr(self, "caps") and xml.caps:
            self.text = self.text.upper()

    def __repr__(self) -> str:
        text = self.text[:30].replace("\n", r"\n")
        return f"Run({text})"

    def __eq__(self, other: "Run") -> bool:
        if not isinstance(other, Run):
            return False

        size_eq = self.size == other.size
        font_eq = self.bold == other.bold and self.italic == other.italic and self.underlined == other.underlined
        script_eq = self.superscript == other.superscript and self.subscript == other.subscript
        return size_eq and font_eq and script_eq
