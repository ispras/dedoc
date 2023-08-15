import re

from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class LetterPrefix(LinePrefix):
    """
    for such items as

    a) first letter
    b) second letter

    or for russian
    а) Moskau — fremd und geheimnisvoll
    б) Türme aus rotem Gold
    в) Kalt wie das Eis
    """

    regexp = re.compile(r"^\s*[а-яёa-z]\)")
    name = "letter"

    @property
    def order(self) -> float:
        letter = self.prefix[0]
        if letter == "ё":  # ё is between е and ж, but ord("ё") is not between them
            return 0.5 * (ord("е") + ord("ж"))
        elif letter == "Ё":  # Ё is between Е and Ж, but ord("Ё") is not between them
            return 0.5 * (ord("Е") + ord("Ж"))
        else:
            return ord(letter)

    def predecessor(self, other: "LinePrefix") -> bool:
        return isinstance(other, LetterPrefix) and 1 >= (self.order - other.order) > 0

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        if len(prefix_str) > 1 and not prefix_str.endswith(")"):
            return False
        return len(prefix_str) > 0 and prefix_str[0].isalpha()
