from typing import Optional, Union

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class DottedListPattern(RegexpPattern):
    """
    Pattern for matching numbered lists with dots, e.g.

    ::

        1. first element
            1.1. first sub-element
            1.2. second sub-element
        2. second element

    The number of dots is unlimited.
    There is no ``level_2`` parameter in this pattern, ``level_2`` is calculated as the number of numbers between dots, e.g.

    * ``1.`` → ``level_2=1``
    * ``1.1`` or ``1.1.`` → ``level_2=2``
    * ``1.2.3.4`` or ``1.2.3.4.`` → ``level_2=4``

    Example of library usage:

    .. code-block:: python

        from dedoc.structure_extractors import DefaultStructureExtractor
        from dedoc.structure_extractors.patterns import DottedListPattern

        reader = ...
        structure_extractor = DefaultStructureExtractor()
        patterns = [DottedListPattern(line_type="list_item", level_1=1, can_be_multiline=False)]
        document = reader.read(file_path=file_path)
        document = structure_extractor.extract(document=document, parameters={"patterns": patterns})

    Example of API usage:

    .. code-block:: python

        import requests

        patterns = [{"name": "dotted_list", "line_type": "list_item", "level_1": 1, "can_be_multiline": "false"}]
        parameters = {"patterns": str(patterns)}
        with open(file_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post("http://localhost:1231/upload", files=files, data=parameters)
    """
    _name = "dotted_list"

    def __init__(self, line_type: str, level_1: int, can_be_multiline: Optional[Union[bool, str]] = None) -> None:
        super().__init__(regexp=DottedPrefix.regexp, line_type=line_type, level_1=level_1, level_2=None, can_be_multiline=can_be_multiline)

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=self._line_type,
            level_1=self._level_1,
            level_2=self.__get_list_depth(line=line),
            can_be_multiline=self._can_be_multiline
        )

    def __get_list_depth(self, line: LineWithMeta) -> int:
        text = line.line.strip().lower()
        match = self._regexp.match(text)
        if match is None:
            raise ValueError(f'Line text "{text}" does not match dotted list pattern regexp')

        prefix = match.group().strip()
        return len([number for number in prefix.split(".") if len(number) > 0])
