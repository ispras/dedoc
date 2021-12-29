from typing import Optional, List
import re

from bs4 import BeautifulSoup

from dedoc.readers.docx_reader.data_structures.base_props import BaseProperties
from dedoc.readers.docx_reader.data_structures.run import Run
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties


class StylesExtractor:

    def __init__(self,
                 xml: BeautifulSoup):
        """
        :param xml: BeautifulSoup tree with styles
        """
        if xml:
            self.styles = xml.styles
            if not self.styles:
                raise Exception("there are no styles")
        else:
            raise Exception("xml must not be empty")
        self.numbering_extractor = None
        # extract information from docDefaults
        # docDefaults: rPrDefault + pPrDefault
        self.doc_defaults = self.styles.docDefaults
        self.default_style = self.styles.find_all('w:style', attrs={'w:default': "1", 'w:type': "paragraph"})
        if self.default_style:
            self.default_style = self.default_style[0]
        else:
            self.default_style = None
        self.__cache = {}

    def _find_style(self,
                    style_id: str,
                    style_type: str) -> Optional[BeautifulSoup]:
        """
        finds style tree with given style_id and style_type
        :param style_id: styleId for given style
        :param style_type: "paragraph" or "character"
        :return: None if there isn't such style else BeautifulSoup tree with style
        """
        key = (style_id, style_type)
        if key in self.__cache:
            return self.__cache[key]
        styles = self.styles.find_all('w:style', attrs={'w:styleId': style_id, 'w:type': style_type})
        if styles:
            result = styles[0]
            self.__cache[key] = result
            return result
        return None

    def parse(self,
              style_id: Optional[str],
              old_properties: BaseProperties,
              style_type: str):
        """
        if style_id is None finds default style
        else finds style with given style_id and changes
        old_properties according to style's properties
        :param style_id: styleId for style
        :param old_properties: properties for saving style properties
        :param style_type: "paragraph" or "character" or "numbering" (auxiliary, it will be changed as "paragraph")
        """

        # TODO firstLineChars etc.
        # TODO link
        # TODO suppressLineNumbers

        if self.doc_defaults:
            change_paragraph_properties(old_properties, self.doc_defaults)
        if self.default_style:
            change_paragraph_properties(old_properties, self.default_style)

        # if styleId == None set default style
        if not style_id:
            return

        # it is used for prevent recursion because of style and numbering linking
        if style_type == "numbering":
            ignore_num = True
            style_type = "paragraph"
        else:
            ignore_num = False

        style = self._find_style(style_id, style_type)
        if not style:
            return

        if hasattr(old_properties, "style_name"):
            name = style.find("w:name")
            if name:
                old_properties.style_name = name["w:val"].lower()
            else:
                old_properties.style_name = style_id.lower()
            old_properties.style_level = self._get_style_level(old_properties.style_name)

        styles = self._get_styles_hierarchy(style, style_type)

        self._apply_styles(old_properties, styles)

        # information in numPr for styles
        if style.numPr and self.numbering_extractor and hasattr(old_properties, "xml") and \
                not old_properties.xml.numPr and not ignore_num:
            try:
                numbering_run = Run(old_properties, self)
                self.numbering_extractor.parse(style, old_properties, numbering_run)
                if hasattr(old_properties, 'runs'):
                    old_properties.runs.append(numbering_run)
            except KeyError as error:
                print(error)

    @staticmethod
    def _apply_styles(old_properties: BaseProperties,
                      styles: List[BeautifulSoup]):
        """
        applies all styles to old_properties
        :param old_properties: properties for changing
        :param styles: styles in order to apply
        """
        # hierarchy of styles: defaults -> paragraph -> numbering -> character
        for current_style in styles:  # apply styles in reverse order
            if current_style.pPr:
                change_paragraph_properties(old_properties, current_style.pPr)
            if current_style.rPr:
                change_run_properties(old_properties, current_style.rPr)

    def _get_styles_hierarchy(self,
                              style: BeautifulSoup,
                              style_type: str) -> List[BeautifulSoup]:
        """
        makes the list with styles hierarchy
        :param style: the first style in the hierarchy
        :returns: the list with styles hierarchy
        """
        styles = [style]
        # basedOn + hierarchy of styles
        current_style = style
        while current_style.basedOn:
            try:
                parent_style_id = current_style.basedOn['w:val']
                current_style = self._find_style(parent_style_id, style_type)
                if current_style:
                    styles.append(current_style)
            except KeyError:
                pass
        styles = styles[::-1] + [style]
        return styles

    @staticmethod
    def _get_style_level(style_name: str) -> Optional[int]:
        """
        :param style_name: name of the style
        :returns: level if style name begins with heading else None
        """
        if re.match(r'heading \d', style_name):
            return int(style_name[len("heading "):]) - 1
        return None
