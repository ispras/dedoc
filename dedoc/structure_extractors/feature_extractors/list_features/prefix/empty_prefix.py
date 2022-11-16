from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class EmptyPrefix(LinePrefix):

    """
    Line without ''list like'' prefix, it is some kind of zero for prefixes
    """
    name = "empty"

    def __init__(self, prefix: str = None, indent: float = 0) -> None:
        super().__init__("", indent=indent)

    def predecessor(self, other: "LinePrefix") -> bool:
        return False

    @staticmethod
    def is_valid(prefix_str: str) -> bool:
        return True
