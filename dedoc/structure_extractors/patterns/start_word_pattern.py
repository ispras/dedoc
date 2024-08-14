from typing import Optional

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class StartWordPattern(AbstractPattern):
    __name = "start_word"

    def __init__(self,
                 start_word: str,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[bool] = None) -> None:
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
        self.__start_word = start_word.strip().lower()

    def match(self, line: LineWithMeta) -> bool:
        text = line.line.strip().lower()
        return text.startswith(self.__start_word)
