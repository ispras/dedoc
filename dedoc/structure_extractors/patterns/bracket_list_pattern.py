from typing import Optional

from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class BracketListPattern(RegexpPattern):
    __name = "bracket_list"

    def __init__(self, line_type: str, level_1: int, level_2: Optional[int] = None, can_be_multiline: bool = False) -> None:
        super().__init__(regexp=BracketPrefix.regexp, line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
