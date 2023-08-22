import re

from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class BracketPrefix(LinePrefix):
    """
    Prefix for list with numbers with bracket

    1) first element
    2) second element
    """

    regexp = re.compile(r"^\s*\d\)")
    name = "bracket"

    def __init__(self, prefix: str, indent: float) -> None:
        super().__init__(prefix, indent=indent)
        self.prefix_num = int(self.prefix[:-1])

    def predecessor(self, other: "LinePrefix") -> bool:
        return isinstance(other, BracketPrefix) and self.prefix_num == other.prefix_num + 1

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        return len(prefix_str) > 1 and prefix_str[:-1].isdigit() and prefix_str.endswith(")")
