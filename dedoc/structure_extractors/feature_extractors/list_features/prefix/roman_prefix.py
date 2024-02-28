import re

import roman

from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class RomanPrefix(LinePrefix):
    """
    for such items as

    I. first item
    II. second item
    III. third item
    IV. forth item
    """

    regexp = re.compile(r"^\s*[ivxl]\.")
    name = "roman"

    def __init__(self, prefix: str, indent: float) -> None:
        prefix = prefix.lower()
        super().__init__(prefix, indent=indent)
        self.prefix_num = roman.fromRoman(self.prefix[:-1].upper().strip())

    def predecessor(self, other: "LinePrefix") -> bool:
        return isinstance(other, RomanPrefix) and self.prefix_num == other.prefix_num + 1

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        prefix_str = prefix_str.lower()
        if len(prefix_str) <= 1 or not prefix_str.endswith("."):
            return False
        prefix_set = set(prefix_str[:-1])
        return prefix_set.issubset(set("ivxl"))
