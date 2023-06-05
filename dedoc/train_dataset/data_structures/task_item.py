from collections import OrderedDict
from typing import Optional, List

from dedoc.data_structures.serializable import Serializable


class TaskItem(Serializable):

    def __init__(self,
                 task_id: int,
                 task_path: str,
                 data: any,
                 labeled: Optional[List[str]],
                 additional_info: str = "",
                 default_label: str = None) -> None:
        """

        @param task_id: id of this item. unique in one task
        @param task_path: relative path to image
        @param data: any data, (features, comments and so on, it should not be used in annotation process and flow to
        the result as is)
        @param additional_info: Optional, info for annotators, for example line num, page num or some kind of that
        @param labeled: Optional, predicted classes for this item.
        """
        self.task_id = task_id
        self.task_path = task_path
        self.data = data
        self.labeled = labeled if labeled is not None else []
        self.additional_info = additional_info
        self.default_label = default_label

    def to_dict(self, old_version: bool = False) -> dict:
        result = OrderedDict()
        result["id"] = self.task_id
        result["task_path"] = self.task_path
        if self.labeled is not None:
            result["labeled"] = self.labeled
        result["data"] = self.data
        result["additional_info"] = self.additional_info
        if self.default_label:
            result["default_label"] = self.default_label
        return result
