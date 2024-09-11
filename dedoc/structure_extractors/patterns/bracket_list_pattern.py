from typing import Optional, Union

from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class BracketListPattern(RegexpPattern):
    """
    Pattern for matching numbered lists with brackets, e.g.

    ::

        1) first element
        2) second element

    Example of library usage:

    .. code-block:: python

        from dedoc.structure_extractors import DefaultStructureExtractor
        from dedoc.structure_extractors.patterns import BracketListPattern

        reader = ...
        structure_extractor = DefaultStructureExtractor()
        patterns = [BracketListPattern(line_type="list_item", level_1=1, level_2=1, can_be_multiline=False)]
        document = reader.read(file_path=file_path)
        document = structure_extractor.extract(document=document, parameters={"patterns": patterns})

    Example of API usage:

    .. code-block:: python

        import requests

        patterns = [{"name": "bracket_list", "line_type": "list_item", "level_1": 1, "level_2": 1, "can_be_multiline": "false"}]
        parameters = {"patterns": str(patterns)}
        with open(file_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post("http://localhost:1231/upload", files=files, data=parameters)
    """
    _name = "bracket_list"

    def __init__(self, line_type: str, level_1: int, level_2: int, can_be_multiline: Optional[Union[bool, str]] = None) -> None:
        super().__init__(regexp=BracketPrefix.regexp, line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)