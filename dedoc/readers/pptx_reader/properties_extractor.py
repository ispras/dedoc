from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from bs4 import Tag


@dataclass
class Properties:
    bold: bool = False
    italic: bool = False
    underlined: bool = False
    superscript: bool = False
    subscript: bool = False
    strike: bool = False
    size: int = 0
    alignment: str = "left"
    title: bool = False


class PropertiesExtractor:
    """
    Properties hierarchy:

    - Run and paragraph properties (slide.xml)
    - Slide layout properties (slideLayout.xml)
    - Master slide properties (slideMaster.xml)
    - Presentation default properties (presentation.xml -> defaultTextStyle)
    """
    def __init__(self, file_path: str) -> None:
        self.alignment_mapping = dict(l="left", r="right", ctr="center", just="both", dist="both", justLow="both", thaiDist="both")
        self.lvl2properties = self.__get_properties_mapping(file_path)

    def get_properties(self, xml: Tag, level: int, properties: Optional[Properties] = None) -> Properties:
        """
        xml examples:
            <a:pPr indent="0" lvl="0" marL="0" rtl="0" algn="l">
            <a:rPr i="1" lang="ru" sz="1800">
            <a:rPr baseline="30000" lang="ru" sz="1800">
        """
        new_properties = deepcopy(properties) or self.lvl2properties.get(level, Properties())
        if not xml:
            return new_properties

        if int(xml.get("b", "0")):
            new_properties.bold = True
        if int(xml.get("i", "0")):
            new_properties.italic = True

        underlined = xml.get("u", "none").lower()
        if underlined != "none":
            new_properties.underlined = True

        strike = xml.get("strike", "nostrike").lower()
        if strike != "nostrike":
            new_properties.strike = True

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

    def __get_properties_mapping(self, file_path: str) -> Dict[int, Properties]:
        pass
