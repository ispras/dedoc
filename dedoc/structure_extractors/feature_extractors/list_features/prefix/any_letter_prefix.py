import re

from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class AnyLetterPrefix(LinePrefix):
    """
    Prefix for bracket lists for any language:

    a) bla
    b) bla bla

    ա) տեղաբաշխել
    բ) Հայաստանի Հանրապետության
    գ) սահմանապահ վերակարգերի

    and so on
    """
    name = "any_letter"

    regexp = re.compile(r"^\s*\w\)")

    def predecessor(self, other: "LinePrefix") -> bool:
        return isinstance(other, AnyLetterPrefix)

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        if len(prefix_str) > 1 and not prefix_str.endswith(")"):
            return False
        return len(prefix_str) > 0
