import re

from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class BulletPrefix(LinePrefix):
    """
    Prefix for all kind of dotted lists:

    * first letter
    * second letter

    - first item
    - second item

    and so on
    """
    name = "non_letter"

    regexp = re.compile(r"^\s*(-|—|−|–|®|\.|•|\,|‚|©|⎯|°|\*|>|\| -|●|♣|①|▪|\*|\+)")

    def predecessor(self, other: "LinePrefix") -> bool:
        return isinstance(other, BulletPrefix) and self.prefix == other.prefix

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        if BulletPrefix.regexp.fullmatch(prefix_str):
            return True
        return len(prefix_str) == 1 and not prefix_str.isalnum() and not prefix_str.isspace()
