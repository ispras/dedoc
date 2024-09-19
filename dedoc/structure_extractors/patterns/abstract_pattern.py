from abc import ABC, abstractmethod
from typing import Optional, Union

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractPattern(ABC):
    """
    Base class for all patterns to configure structure extraction by :class:`~dedoc.structure_extractors.DefaultStructureExtractor`.
    """
    _name = ""

    def __init__(self, line_type: Optional[str], level_1: Optional[int], level_2: Optional[int], can_be_multiline: Optional[Union[bool, str]]) -> None:
        """
        Initialize pattern with default values of :class:`~dedoc.data_structures.HierarchyLevel` attributes.
        They can be used in :meth:`~dedoc.structure_extractors.patterns.abstract_pattern.AbstractPattern.get_hierarchy_level`
        according to specific pattern logic.

        :param line_type: type of the line, e.g. "header", "bullet_list_item", "chapter", etc.
        :param level_1: value of a line primary importance
        :param level_2: level of the line inside specific class
        :param can_be_multiline: is used to unify lines inside tree node by :class:`~dedoc.structure_constructors.TreeConstructor`,
            if line can be multiline, it can be joined with another line. If ``None`` is given, can_be_multiline is set to ``True``.
        """
        from dedoc.utils.parameter_utils import get_bool_value

        self._line_type = line_type
        self._level_1 = level_1
        self._level_2 = level_2
        self._can_be_multiline = get_bool_value(can_be_multiline, default_value=True)

    @classmethod
    def name(cls: "AbstractPattern") -> str:
        """
        Returns ``_name`` attribute, is used in parameters configuration to choose a specific pattern.
        Each pattern has a unique non-empty name.
        """
        return cls._name

    @abstractmethod
    def match(self, line: LineWithMeta) -> bool:
        """
        Check if the given line satisfies to the pattern requirements.
        Line text, annotations or metadata (``metadata.tag_hierarchy_level``) can be used to decide, if the line matches the pattern or not.
        """
        pass

    @abstractmethod
    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        """
        This method should be applied only when :meth:`~dedoc.structure_extractors.patterns.abstract_pattern.AbstractPattern.match`
        returned ``True`` for the given line.

        Get :class:`~dedoc.data_structures.HierarchyLevel` for initialising ``line.metadata.hierarchy_level`` attribute.
        Please see :ref:`add_structure_type_hierarchy_level` to get more information about :class:`~dedoc.data_structures.HierarchyLevel`.
        """
        pass
