from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractPattern(ABC):
    _name = ""

    def __init__(self, line_type: Optional[str], level_1: Optional[int], level_2: Optional[int], can_be_multiline: Optional[bool or str]) -> None:
        from dedoc.utils.parameter_utils import get_bool_value

        self._line_type = line_type
        self._level_1 = level_1
        self._level_2 = level_2
        self._can_be_multiline = get_bool_value(can_be_multiline, default_value=True)

    @classmethod
    def name(cls: "AbstractPattern") -> str:
        return cls._name

    @abstractmethod
    def match(self, line: LineWithMeta) -> bool:
        pass

    @abstractmethod
    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        pass
