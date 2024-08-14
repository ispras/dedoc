from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractPattern(ABC):
    _name = ""

    def __init__(self,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[bool] = None) -> None:
        self._line_type = line_type
        self._level_1 = level_1
        self._level_2 = level_2
        self._can_be_multiline = can_be_multiline

    @classmethod
    def name(cls: "AbstractPattern") -> str:
        return cls._name

    @abstractmethod
    def match(self, line: LineWithMeta) -> bool:
        pass

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=self._get_line_type(line),
            level_1=self._get_level_1(line),
            level_2=self._get_level_2(line),
            can_be_multiline=self._get_can_be_multiline(line)
        )

    def _get_line_type(self, line: LineWithMeta) -> str:
        if self._line_type is not None:
            return self._line_type

        if line.metadata.tag_hierarchy_level is None:
            raise ValueError(f"Cannot resolve line type: tag_hierarchy_level is missing and {self._name} line_type isn't configured")

        return line.metadata.tag_hierarchy_level.line_type

    def _get_level_1(self, line: LineWithMeta) -> Optional[int]:
        if self._level_1 is not None:
            return self._level_1

        return line.metadata.tag_hierarchy_level.level_1 if line.metadata.tag_hierarchy_level else None

    def _get_level_2(self, line: LineWithMeta) -> Optional[int]:
        if self._level_2 is not None:
            return self._level_2

        return line.metadata.tag_hierarchy_level.level_2 if line.metadata.tag_hierarchy_level else None

    def _get_can_be_multiline(self, line: LineWithMeta) -> bool:
        if self._can_be_multiline is not None:
            return self._can_be_multiline

        return line.metadata.tag_hierarchy_level.can_be_multiline if line.metadata.tag_hierarchy_level else True
