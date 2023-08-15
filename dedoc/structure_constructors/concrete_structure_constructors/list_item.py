from typing import List


LIST_ITEM_POINT_END_TYPE = "."
LIST_ITEM_BRACKET_END_TYPE = ")"


class ListItem:
    def __init__(self, item: List[int], end: str) -> None:
        self.item = item
        self.end_type = LIST_ITEM_BRACKET_END_TYPE if end == ")" else LIST_ITEM_POINT_END_TYPE

    def get_parent(self) -> "ListItem":
        parent_item = [item for item in self.item]
        parent_item[-1] -= 1

        if parent_item[-1] <= 0:
            parent_item.pop()

        return ListItem(parent_item, self.end_type)

    def __lt__(self, item: "ListItem") -> bool:
        if self.end_type != item.end_type:
            return False

        max_len = max(len(self.item), len(item.item))

        for i in range(max_len):
            d1 = self.item[i] if i < len(self.item) else 0
            d2 = item.item[i] if i < len(item.item) else 0

            if d1 != d2:
                return d1 < d2

        return False

    def __eq__(self, item: "ListItem") -> bool:
        return self.item == item.item and self.end_type == item.end_type

    def __ne__(self, item: "ListItem") -> bool:
        return self.item != item.item or self.end_type != item.end_type

    def is_first_item(self) -> bool:
        return self.item == [1]

    def __str__(self) -> str:
        return ".".join([str(item) for item in self.item]) + self.end_type
