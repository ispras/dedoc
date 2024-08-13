from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractPattern(ABC):
    __name = ""

    def __init__(self, line_type: str, level_1: int, level_2: Optional[int] = None, can_be_multiline: bool = False) -> None:
        self._line_type = line_type
        self._level_1 = level_1
        self._level_2 = level_2 if level_2 else 1
        self._can_be_multiline = can_be_multiline

    @classmethod
    def name(cls: "AbstractPattern") -> str:
        return cls.__name

    @abstractmethod
    def match(self, line: LineWithMeta) -> bool:
        pass

    @abstractmethod
    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        pass
