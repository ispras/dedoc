from functools import total_ordering
from typing import Optional


@total_ordering
class HierarchyLevel:

    paragraph = "paragraph"
    raw_text = "raw_text"
    list_item = "list_item"

    def __init__(self, level_1: Optional[int], level_2: Optional[int], can_be_multiline: bool, paragraph_type: str):
        self.level_1 = level_1
        self.level_2 = level_2
        self.can_be_multiline = can_be_multiline
        self.paragraph_type = paragraph_type

        assert paragraph_type == HierarchyLevel.raw_text or (level_1 is not None and level_2 is not None)

    def __eq__(self, other: "HierarchyLevel") -> bool:
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return True
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type != HierarchyLevel.raw_text:
            return False
        if self.paragraph_type != HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return False
        if (self.level_1, self.level_2) == (other.level_1, other.level_2):
            return True
        return False

    def __lt__(self, other: "HierarchyLevel") -> bool:
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return False
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type != HierarchyLevel.raw_text:
            return False
        if self.paragraph_type != HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return True
        return (self.level_1, self.level_2) < (other.level_1, other.level_2)

    def is_raw_text(self) -> bool:
        return self.paragraph_type == HierarchyLevel.raw_text

    def is_list_item(self) -> bool:
        return self.paragraph_type == HierarchyLevel.list_item

    @staticmethod
    def create_raw_text() -> "HierarchyLevel":
        return HierarchyLevel(level_1=None,
                              level_2=None,
                              can_be_multiline=False,
                              paragraph_type=HierarchyLevel.raw_text)

