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
    def __init__(self, xml: Tag) -> None:
        self.xml = xml

    def get_properties(self, properties: Optional[Properties] = None) -> Properties:
        new_properties = deepcopy(properties) or Properties()
        return new_properties
