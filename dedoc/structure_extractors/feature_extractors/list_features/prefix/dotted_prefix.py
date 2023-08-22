import re

from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class DottedPrefix(LinePrefix):

    regexp = re.compile(r"^\s*(\d+\.)+(\d+)?\s*")
    name = "dotted"

    def __init__(self, prefix: str, indent: float) -> None:
        super().__init__(prefix, indent=indent)
        self.numbers = [int(n) for n in self.prefix.split(".") if len(n) > 0]

    def predecessor(self, other: "DottedPrefix") -> bool:
        if not isinstance(other, DottedPrefix):
            return False
        if len(self.numbers) == len(other.numbers):
            for n1, n2 in zip(self.numbers[:-1], other.numbers[:-1]):
                if n1 != n2:
                    return False
            n1, n2 = self.numbers[-1], other.numbers[-1]
            return n1 - n2 == 1
        if len(self.numbers) == 1 + len(other.numbers):
            for n1, n2 in zip(self.numbers, other.numbers):
                if n1 != n2:
                    return False
            return self.numbers[-1] == 1
        if len(other.numbers) > len(self.numbers):
            for n1, n2 in zip(self.numbers[:-1], other.numbers[:-1]):
                if n1 != n2:
                    return False
            return self.numbers[-1] == other.numbers[len(self.numbers) - 1] + 1
        return False

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        return len(prefix_str) > 0 and all(_.isdigit() for _ in prefix_str.split(".") if _)
