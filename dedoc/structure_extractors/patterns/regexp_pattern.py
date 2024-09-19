import re
from typing import Optional, Union

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class RegexpPattern(AbstractPattern):
    """
    Pattern for matching line text by a regular expression.

    .. note::

        The pattern is case-insensitive (lower and upper letters are not differed).
        Before regular expression matching, the line text is stripped (space symbols are deleted from both sides).

    .. seealso::

        Syntax for writing regular expressions is described in the `Python documentation <https://docs.python.org/3/library/re.html>`_.

    Example of library usage:

    .. code-block:: python

        import re
        from dedoc.structure_extractors import DefaultStructureExtractor
        from dedoc.structure_extractors.patterns import RegexpPattern

        reader = ...
        structure_extractor = DefaultStructureExtractor()
        patterns = [
            RegexpPattern(regexp="^chapter\s\d+\.", line_type="chapter", level_1=1, can_be_multiline=False),
            RegexpPattern(regexp=re.compile(r"^part\s\d+\.\d+\."), line_type="part", level_1=2, can_be_multiline=False)
        ]
        document = reader.read(file_path=file_path)
        document = structure_extractor.extract(document=document, parameters={"patterns": patterns})

    Example of API usage:

    .. code-block:: python

        import requests

        patterns = [{"name": "regexp", "regexp": "^chapter\s\d+\.", "line_type": "chapter", "level_1": 1, "can_be_multiline": "false"}]
        parameters = {"patterns": str(patterns)}
        with open(file_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post("http://localhost:1231/upload", files=files, data=parameters)
    """ # noqa
    _name = "regexp"

    def __init__(self,
                 regexp: str or re.Pattern,
                 line_type: str,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[Union[bool, str]] = None) -> None:
        """
        Initialize pattern with default values of :class:`~dedoc.data_structures.HierarchyLevel` attributes.

        :param regexp: regular expression for checking, if the line text matches the pattern.
            Note that regular expression is used on the lowercase and stripped line.
        :param line_type: type of the line, e.g. "header", "bullet_list_item", "chapter", etc.
        :param level_1: value of a line primary importance
        :param level_2: level of the line inside specific class
        :param can_be_multiline: is used to unify lines inside tree node by :class:`~dedoc.structure_constructors.TreeConstructor`,
            if line can be multiline, it can be joined with another line. If ``None`` is given, can_be_multiline is set to ``True``.
        """
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
        self._regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def match(self, line: LineWithMeta) -> bool:
        """
        Check if the pattern is suitable for the given line.
        Line text is checked by applying pattern's regular expression, text is stripped and made lowercase beforehand.
        """
        text = line.line.strip().lower()
        match = self._regexp.match(text)
        return match is not None

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        """
        This method should be applied only when :meth:`~dedoc.structure_extractors.patterns.RegexpPattern.match`
        returned ``True`` for the given line.

        Return :class:`~dedoc.data_structures.HierarchyLevel` for initialising ``line.metadata.hierarchy_level``.
        The attributes ``line_type``, ``level_1``, ``level_2``, ``can_be_multiline`` are equal to values given during class initialisation.
        """
        return HierarchyLevel(line_type=self._line_type, level_1=self._level_1, level_2=self._level_2, can_be_multiline=self._can_be_multiline)
