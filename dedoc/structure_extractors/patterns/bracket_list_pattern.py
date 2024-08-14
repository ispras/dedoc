from typing import Optional

from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class BracketListPattern(RegexpPattern):
    _name = "bracket_list"

    def __init__(self,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[bool] = None) -> None:
        super().__init__(regexp=BracketPrefix.regexp, line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
