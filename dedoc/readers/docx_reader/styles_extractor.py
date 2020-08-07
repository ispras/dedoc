from bs4 import BeautifulSoup
from dedoc.readers.docx_reader.properties_extractor import change_properties
from dedoc.readers.docx_reader.data_structures import BaseProperties, Raw

# page 665 in documentation


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

    def find_style(self,
                   style_id: str,
                   style_type: str):
        """
        finds style tree with given style_id and style_type
        :param style_id: styleId for given style
        :param style_type: "paragraph" or "character"
        :return: None if there isn't such style else BeautifulSoup tree with style
        """
        styles = self.styles.find_all('w:style', attrs={'w:styleId': style_id})
        result_style = None
        for style in styles:
            try:
                if style['w:type'] == style_type:
                    return style
            except KeyError:
                result_style = style
        return result_style

    def parse(self,
              style_id: str or None,
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
        # if tag b, i presents, but there isn't its value, then w:val = '1'
        # for tag u value = 'none'
        # for indent and size value = 0

        # TODO firstLineChars etc.
        # TODO link
        # TODO suppressLineNumbers

        # if styleId == None set default style
        # TODO numPr in default style
        if not style_id:
            if self.doc_defaults:
                change_properties(old_properties, self.doc_defaults)
            if self.default_style:
                change_properties(old_properties, self.default_style)
            return

        # TODO solve this more correctly
        # it is used for prevent recursion because of style and numbering linking
        if style_type == "numbering":
            ignore_num = True
            style_type = "paragraph"
        else:
            ignore_num = False

        styles = []
        style = self.find_style(style_id, style_type)
        if not style:
            return

        # basedOn + hierarchy of styles
        current_style = style
        while current_style.basedOn:
            try:
                parent_style_id = current_style.basedOn['w:val']
                current_style = self.find_style(parent_style_id, style_type)
                if current_style:
                    styles.append(current_style)
            except KeyError:
                pass

        styles = styles[::-1] + [style]
        if self.default_style:
            styles = [self.doc_defaults, self.default_style] + styles

        # hierarchy of styles: defaults -> paragraph -> numbering -> character
        for current_style in styles:  # apply styles in reverse order
            if current_style.pPr:
                change_properties(old_properties, current_style.pPr)
            if current_style.rPr:
                change_properties(old_properties, current_style.rPr)
                old_properties.r_pr = current_style.rPr

        # information in numPr for styles
        if style.numPr and self.numbering_extractor and not old_properties.xml.numPr and not ignore_num:
            try:
                numbering_raw = Raw(old_properties, self)
                self.numbering_extractor.parse(style, old_properties, numbering_raw)
                if hasattr(old_properties, 'raws'):
                    old_properties.raws.append(numbering_raw)
            except KeyError as error:
                print(error)
