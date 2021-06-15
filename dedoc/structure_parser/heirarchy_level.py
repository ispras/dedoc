from functools import total_ordering
from typing import Optional


@total_ordering
class HierarchyLevel:
    paragraph = "paragraph"
    raw_text = "raw_text"
    list_item = "list_item"
    root = "root"

    def __init__(self, level_1: Optional[int], level_2: Optional[int], can_be_multiline: bool, paragraph_type: str):
        assert level_1 is None or level_1 >= 0
        assert level_2 is None or level_2 >= 0
        self.level_1 = level_1
        self.level_2 = level_2
        self.can_be_multiline = can_be_multiline
        self.paragraph_type = paragraph_type

        assert paragraph_type == HierarchyLevel.raw_text or (level_1 is not None and level_2 is not None)

    def __is_defined(self, other: "HierarchyLevel") -> bool:
        return (self.level_1 is not None and
                self.level_2 is not None and
                other.level_1 is not None and
                other.level_2 is not None)

    def __eq__(self, other: "HierarchyLevel") -> bool:
        if self.__is_defined(other) and (self.level_1, self.level_2) == (other.level_1, other.level_2):
            return True
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return True
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type != HierarchyLevel.raw_text:
            return False
        if self.paragraph_type != HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return False
        return False

    def __lt__(self, other: "HierarchyLevel") -> bool:
        if self.__is_defined(other):
            return (self.level_1, self.level_2) < (other.level_1, other.level_2)
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return False
        if self.paragraph_type == HierarchyLevel.raw_text and other.paragraph_type != HierarchyLevel.raw_text:
            return False
        if self.paragraph_type != HierarchyLevel.raw_text and other.paragraph_type == HierarchyLevel.raw_text:
            return True
        return (self.level_1, self.level_2) < (other.level_1, other.level_2)

    def __str__(self):
        return "HierarchyLevel(level_1={}, level_2={}, can_be_multiline={}, paragraph_type={})".format(
            self.level_1, self.level_2, self.can_be_multiline, self.paragraph_type
        )

    def is_raw_text(self) -> bool:
        return self.paragraph_type == HierarchyLevel.raw_text

    def is_list_item(self) -> bool:
        return self.paragraph_type == HierarchyLevel.list_item

    @staticmethod
    def create_raw_text() -> "HierarchyLevel":
        return HierarchyLevel(level_1=None,
                              level_2=None,
                              can_be_multiline=True,
                              paragraph_type=HierarchyLevel.raw_text)

    @staticmethod
    def create_root() -> "HierarchyLevel":
        return HierarchyLevel(level_1=0, level_2=0, can_be_multiline=True, paragraph_type=HierarchyLevel.root)
