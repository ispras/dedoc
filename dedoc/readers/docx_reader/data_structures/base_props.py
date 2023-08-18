from typing import Optional


class BaseProperties:

    def __init__(self, properties: Optional["BaseProperties"] = None) -> None:  # noqa
        """
        Contains style properties for paragraphs and runs.
        :param properties: Paragraph or Run for copying its properties
        """
        self.jc = properties.jc if properties else "left"
        self.indentation = properties.indentation if properties and properties.indentation else 0
        self.size = properties.size if properties else 0
        self.bold = properties.bold if properties else False
        self.italic = properties.italic if properties else False
        self.underlined = properties.underlined if properties else False
        self.strike = properties.strike if properties else False
        self.superscript = properties.superscript if properties else False
        self.subscript = properties.subscript if properties else False
