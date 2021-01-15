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
            if properties.indent:
                self.indent = properties.indent.copy()
            else:
                self.indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0}
            self.size = properties.size
            self.bold = properties.bold
            self.italic = properties.italic
            self.underlined = properties.underlined
            properties.underlined = properties.underlined
        else:
            self.jc = 'left'
            self.indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0}
            self.size = 0
            self.bold = False
            self.italic = False
            self.underlined = False
        self.styles_extractor = styles_extractor
