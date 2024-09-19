from typing import Optional, Union

from dedoc.structure_extractors.feature_extractors.list_features.prefix.any_letter_prefix import AnyLetterPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class LetterListPattern(RegexpPattern):
    """
    Pattern for matching lists with letters and brackets, e.g.

    ::

        a) first element
        b) second element

    or (example for Armenian language)

    ::

        ա) տեղաբաշխել
        բ) Հայաստանի Հանրապետության
        գ) սահմանապահ վերակարգերի

    .. note::

        The pattern is case-insensitive (lower and upper letters are not differed).

    Example of library usage:

    .. code-block:: python

        from dedoc.structure_extractors import DefaultStructureExtractor
        from dedoc.structure_extractors.patterns import LetterListPattern

        reader = ...
        structure_extractor = DefaultStructureExtractor()
        patterns = [LetterListPattern(line_type="list_item", level_1=1, level_2=1, can_be_multiline=False)]
        document = reader.read(file_path=file_path)
        document = structure_extractor.extract(document=document, parameters={"patterns": patterns})

    Example of API usage:

    .. code-block:: python

        import requests

        patterns = [{"name": "letter_list", "line_type": "list_item", "level_1": 1, "level_2": 1, "can_be_multiline": "false"}]
        parameters = {"patterns": str(patterns)}
        with open(file_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post("http://localhost:1231/upload", files=files, data=parameters)
    """
    _name = "letter_list"

    def __init__(self, line_type: str, level_1: int, level_2: int, can_be_multiline: Optional[Union[bool, str]] = None) -> None:
        super().__init__(regexp=AnyLetterPrefix.regexp, line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
