from typing import Optional, Union

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.tag_pattern import TagPattern


class TagHeaderPattern(TagPattern):
    """
    Pattern for using information about heading lines (header) from readers saved in ``line.metadata.tag_hierarchy_level``.
    Also allows to calculate ``level_2`` based on dotted list depth (same as in :class:`~dedoc.structure_extractors.patterns.DottedListPattern`)
    **if level_2, tag_hierarchy_level.level_2, default_level_2 are empty**.

    .. seealso::

        Please see :ref:`readers_line_types` to find out which readers can extract lines with type "header".

    Example of library usage:

    .. code-block:: python

        import re
        from dedoc.structure_extractors import DefaultStructureExtractor
        from dedoc.structure_extractors.patterns import TagHeaderPattern

        reader = ...
        structure_extractor = DefaultStructureExtractor()
        patterns = [TagHeaderPattern(line_type="header", level_1=1, can_be_multiline=False)]
        document = reader.read(file_path=file_path)
        document = structure_extractor.extract(document=document, parameters={"patterns": patterns})

    Example of API usage:

    .. code-block:: python

        import requests

        patterns = [{"name": "tag_header", "line_type": "header", "level_1": 1, "can_be_multiline": "False"}]
        parameters = {"patterns": str(patterns)}
        with open(file_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post("http://localhost:1231/upload", files=files, data=parameters)
    """
    _name = "tag_header"

    def __init__(self,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[Union[bool, str]] = None,
                 default_line_type: str = HierarchyLevel.header,
                 default_level_1: int = 1,
                 default_level_2: Optional[int] = None) -> None:
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline, default_line_type=default_line_type,
                         default_level_1=default_level_1, default_level_2=default_level_2)

    def match(self, line: LineWithMeta) -> bool:
        """
        Check if the pattern is suitable for the given line:

        * ``line.metadata.tag_hierarchy_level`` should not be empty;
        * ``line.metadata.tag_hierarchy_level.line_type == "header"``

        ``line.metadata.tag_hierarchy_level`` is filled during reading step,
        please see :ref:`readers_line_types` to find out which readers can extract lines with type "header".
        """
        return line.metadata.tag_hierarchy_level is not None and line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.header

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=self._get_line_type(line),
            level_1=self._get_level_1(line),
            level_2=self._get_regexp_level_2(line),
            can_be_multiline=self._get_can_be_multiline(line)
        )
