from typing import Optional

from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_roman_prefix import BracketRomanPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class BracketRomanListPattern(RegexpPattern):
    _name = "bracket_roman_list"

    def __init__(self, line_type: str, level_1: int, level_2: int, can_be_multiline: Optional[bool or str] = None) -> None:
        super().__init__(regexp=BracketRomanPrefix.regexp, line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
