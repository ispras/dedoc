import re
from typing import Optional

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class RegexpPattern(AbstractPattern):
    _name = "regexp"

    def __init__(self,
                 regexp: str or re.Pattern,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[bool] = None) -> None:
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
        self._regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def match(self, line: LineWithMeta) -> bool:
        text = line.line.strip().lower()
        match = self._regexp.match(text)
        return match is not None
