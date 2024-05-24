from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

from bs4 import Tag


@dataclass
class Properties:
    bold: bool = False
    italic: bool = False
    underlined: bool = False
    superscript: bool = False
    subscript: bool = False
    strikethrough: bool = False
    size: int = 0
    alignment: str = "left"


class PropertiesExtractor:
    def __init__(self) -> None:
        self.alignment_mapping = dict(l="left", r="right", ctr="center", just="both", dist="both", justLow="both", thaiDist="both")

    def get_properties(self, xml: Tag, properties: Optional[Properties] = None) -> Properties:
        """
        xml examples:
            <a:pPr indent="0" lvl="0" marL="0" rtl="0" algn="l">
            <a:rPr i="1" lang="ru" sz="1800">
            <a:rPr baseline="30000" lang="ru" sz="1800">
        """
        new_properties = deepcopy(properties) or Properties()

        if int(xml.get("b", "0")):
            new_properties.bold = True
        if int(xml.get("i", "0")):
            new_properties.italic = True
        if xml.get("u", ""):
            new_properties.underlined = True
        if xml.get("strike", ""):
            new_properties.strikethrough = True

        size = xml.get("sz")
        if size:
            new_properties.size = float(size) / 100

        baseline = xml.get("baseline")
        if baseline:
            if float(baseline) < 0:
                new_properties.subscript = True
            else:
                new_properties.superscript = True

        alignment = xml.get("algn")
        if alignment and alignment in self.alignment_mapping:
            new_properties.alignment = self.alignment_mapping[alignment]

        return new_properties
