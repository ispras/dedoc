import uuid
from typing import Optional

from dedoc.api.schema.table_metadata import TableMetadata as ApiTableMetadata
from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):
    """
    This class holds the information about table unique identifier, rotation angle (if table has been rotated - for images) and so on.
    """
    def __init__(self, page_id: Optional[int], uid: Optional[str] = None, rotated_angle: float = 0.0) -> None:
        """
        :param page_id: number of the page where table starts
        :param uid: unique identifier of the table
        :param rotated_angle: value of the rotation angle by which the table was rotated during recognition
        """
        self.page_id = page_id
        self.uid = str(uuid.uuid4()) if not uid else uid
        self.rotated_angle = rotated_angle

    def to_api_schema(self) -> ApiTableMetadata:
        return ApiTableMetadata(uid=self.uid, page_id=self.page_id, rotated_angle=self.rotated_angle)
