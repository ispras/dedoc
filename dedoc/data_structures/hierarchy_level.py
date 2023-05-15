from functools import total_ordering
from typing import Optional


@total_ordering
class HierarchyLevel:
    """
    This class defines the level of the document line.
    The lower is its value, the more important the line is.

    The level of the line consists of two parts:
        - level_1 defines primary importance (e.g. root - level_1=0, header - level_1=1, etc.);
        - level_2 defines the level inside lines of equal type (e.g. for list items - "1." - level_2=1, "1.1." - level_2=2, etc.).

    For the least important lines like raw_text both levels are None.
    """
    root = "root"
    toc = "toc"
    header = "header"
    toc_item = "toc_item"
    list = "list"
    list_item = "list_item"
    bullet_list_item = "bullet_list_item"
    raw_text = "raw_text"
    footer = "footer"
    page_id = "page_id"
    unknown = "unknown"

    def __init__(self, level_1: Optional[int], level_2: Optional[int], can_be_multiline: bool, line_type: str) -> None:
        """
        :param level_1: value of a line's primary importance
        :param level_2: level of the line inside specific class
        :param can_be_multiline: is used to unify lines inside tree node, if line can be multiline, it can be joined with another line
        :param line_type: type of the line, e.g. raw text, list item, header, etc.
        """
        assert level_1 is None or level_1 >= 0
        assert level_2 is None or level_2 >= 0
        self.level_1 = level_1
        self.level_2 = level_2
        self.can_be_multiline = can_be_multiline
        self.line_type = line_type

    def __is_defined(self, other: "HierarchyLevel") -> bool:
        return self.level_1 is not None and self.level_2 is not None and other.level_1 is not None and other.level_2 is not None

    def __eq__(self, other: "HierarchyLevel") -> bool:
        """
        Defines the equality of two hierarchy levels:
            - two raw text lines or lines with unknown type are equal;
            - two lines with equal level_1, level_2 are equal.
        """
        if not isinstance(other, HierarchyLevel):
            return False

        if self.__is_defined(other) and (self.level_1, self.level_2) == (other.level_1, other.level_2):
            return True
        if self.line_type == HierarchyLevel.raw_text and other.line_type == HierarchyLevel.raw_text:
            return True
        if self.line_type == HierarchyLevel.unknown and other.line_type == HierarchyLevel.unknown:
            return True
        return False

    def __lt__(self, other: "HierarchyLevel") -> bool:
        """
        Defines the comparison of hierarchy levels:
            - line1 < line2 if (level_1, level_2) of line1 <= (level_1, level_2) of line2;
            - line1 < line2 if line2 is raw text or unknown, and line1 has another type.

        Else line1 >= line2.

        :param other: hierarchy level of the line2
        """
        if self.__is_defined(other):
            return (self.level_1, self.level_2) < (other.level_1, other.level_2)
        if self.level_1 is None and self.level_2 is None and other.level_1 is None and other.level_2 is None:
            return False
        if (self.level_1 is None or self.level_2 is None) and (other.level_1 is not None or other.level_2 is not None):
            return False
        if (self.level_1 is not None or self.level_2 is not None) and (other.level_1 is None or other.level_2 is None):
            return True
        return (self.level_1, self.level_2) < (other.level_1, other.level_2)

    def __str__(self) -> str:
        return f"HierarchyLevel(level_1={self.level_1}, level_2={self.level_2}, can_be_multiline={self.can_be_multiline}, line_type={self.line_type})"

    def is_raw_text(self) -> bool:
        """
        Check if the line is raw text.
        """
        return self.line_type == HierarchyLevel.raw_text

    def is_unknown(self) -> bool:
        """
        Check if the type of the line is unknown (only for levels from readers).
        """
        return self.line_type == HierarchyLevel.unknown

    def is_list_item(self) -> bool:
        """
        Check if the line is a list item.
        """
        return self.line_type == HierarchyLevel.list_item

    @staticmethod
    def create_raw_text() -> "HierarchyLevel":
        """
        Create hierarchy level for a raw textual line.
        """
        return HierarchyLevel(level_1=None, level_2=None, can_be_multiline=True, line_type=HierarchyLevel.raw_text)

    @staticmethod
    def create_unknown() -> "HierarchyLevel":
        """
        Create hierarchy level for a line with unknown type.
        """
        return HierarchyLevel(level_1=None, level_2=None, can_be_multiline=True, line_type=HierarchyLevel.unknown)

    @staticmethod
    def create_root() -> "HierarchyLevel":
        """
        Create hierarchy level for the document root.
        """
        return HierarchyLevel(level_1=0, level_2=0, can_be_multiline=True, line_type=HierarchyLevel.root)
