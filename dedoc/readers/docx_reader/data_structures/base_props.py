from typing import Optional


class BaseProperties:

    def __init__(self,
                 styles_extractor: "StylesExtractor",
                 properties: Optional["BaseProperties"] = None):
        """
        contains properties for paragraphs and runs
        jc, indent, size, bold, italic, underlined
        :param styles_extractor: StylesExtractor
        :param properties: Paragraph or Run for copying it's properties
        """
        if properties:
            self.jc = properties.jc
            self.indentation = properties.indentation if properties.indentation else 0
            self.size = properties.size
            self.bold = properties.bold
            self.italic = properties.italic
            self.underlined = properties.underlined
            self.strike = properties.strike
            self.superscript = properties.superscript
            self.subscript = properties.subscript
            self.underlined = properties.underlined
        else:
            self.jc = 'left'
            self.indentation = 0
            self.size = 0
            self.bold = False
            self.italic = False
            self.underlined = False
            self.strike = False
            self.superscript = False
            self.subscript = False
        self.styles_extractor = styles_extractor
