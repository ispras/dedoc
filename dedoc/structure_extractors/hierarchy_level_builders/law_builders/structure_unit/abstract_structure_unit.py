import abc
from typing import Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel


class AbstractStructureUnit(abc.ABC):

    @abc.abstractmethod
    def structure_unit(self, text: str, init_hl_depth: int, previous_hl: Optional[HierarchyLevel]) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        pass
