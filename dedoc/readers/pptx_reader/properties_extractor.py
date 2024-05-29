from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from bs4 import Tag

from dedoc.utils.office_utils import get_bs_from_zip


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
    This class allows to extract some text formatting properties (see class Properties)

    Properties hierarchy:

    - Run and paragraph properties (slide.xml)
    - Slide layout properties (slideLayout.xml) TODO
    - Master slide properties (slideMaster.xml) TODO
    - Presentation default properties (presentation.xml -> defaultTextStyle)
    """
    def __init__(self, file_path: str) -> None:
        self.alignment_mapping = dict(l="left", r="right", ctr="center", just="both", dist="both", justLow="both", thaiDist="both")
        self.lvl2default_properties = self.__get_default_properties_mapping(file_path)

    def get_properties(self, xml: Tag, level: int, properties: Optional[Properties] = None) -> Properties:
        """
        xml examples:
            <a:pPr indent="0" lvl="0" marL="0" rtl="0" algn="l">
            <a:rPr i="1" lang="ru" sz="1800">
            <a:rPr baseline="30000" lang="ru" sz="1800">
        """
        properties = properties or self.lvl2default_properties.get(level, Properties())
        new_properties = deepcopy(properties)
        if not xml:
            return new_properties

        self.__update_properties(xml, new_properties)
        return new_properties

    def __update_properties(self, xml: Tag, properties: Properties) -> None:
        if int(xml.get("b", "0")):
            properties.bold = True
        if int(xml.get("i", "0")):
            properties.italic = True

        underlined = xml.get("u", "none").lower()
        if underlined != "none":
            properties.underlined = True

        strike = xml.get("strike", "nostrike").lower()
        if strike != "nostrike":
            properties.strike = True

        size = xml.get("sz")
        if size:
            properties.size = float(size) / 100

        baseline = xml.get("baseline")
        if baseline:
            if float(baseline) < 0:
                properties.subscript = True
            else:
                properties.superscript = True

        self.__update_alignment(xml, properties)

    def __update_alignment(self, xml: Tag, properties: Properties) -> None:
        alignment = xml.get("algn")
        if alignment and alignment in self.alignment_mapping:
            properties.alignment = self.alignment_mapping[alignment]

    def __get_default_properties_mapping(self, file_path: str) -> Dict[int, Properties]:
        lvl2properties = {}

        presentation_xml = get_bs_from_zip(file_path, "ppt/presentation.xml", remove_spaces=True)
        default_style = presentation_xml.defaultTextStyle
        if not default_style:
            return lvl2properties

        # lvl1pPr - lvl9pPr
        for i in range(1, 10):
            level_xml = getattr(default_style, f"lvl{i}pPr")
            if level_xml:
                self.__update_level_properties(level_xml, lvl2properties)
        return lvl2properties

    def __update_level_properties(self, xml: Tag, lvl2properties: Dict[int, Properties]) -> None:
        """
        Example:
            <a:lvl1pPr lvl="0" marR="0" rtl="0" algn="l">
                <a:lnSpc><a:spcPct val="100000"/></a:lnSpc>
                <a:spcBef><a:spcPts val="0"/></a:spcBef>
                <a:spcAft><a:spcPts val="0"/></a:spcAft>
                <a:buClr><a:srgbClr val="000000"/></a:buClr>
                <a:buFont typeface="Arial"/>
                <a:defRPr b="0" i="0" sz="1400" u="none" cap="none" strike="noStrike">
                    <a:solidFill><a:srgbClr val="000000"/></a:solidFill>
                    <a:latin typeface="Arial"/>
                    <a:ea typeface="Arial"/>
                    <a:cs typeface="Arial"/>
                    <a:sym typeface="Arial"/>
                </a:defRPr>
            </a:lvl1pPr>
        """
        level = int(xml.get("lvl", "0")) + 1
        level_properties = lvl2properties.get(level, Properties())
        self.__update_alignment(xml, level_properties)
        if xml.defRPr:
            self.__update_properties(xml.defRPr, level_properties)

        lvl2properties[level] = level_properties
