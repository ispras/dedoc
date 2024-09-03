from typing import Optional

from dedoc.api.schema.table_metadata import TableMetadata as ApiTableMetadata
from dedoc.data_structures.serializable import Serializable


class TableMetadata(Serializable):
    """
    This class holds the information about table unique identifier, rotation angle (if table has been rotated - for images) and so on.

    :ivar page_id: number of the page where table starts
    :ivar uid: unique identifier of the table (used for linking table to text)
    :ivar rotated_angle: value of the rotation angle by which the table was rotated during recognition
    :ivar title: table's title

    :vartype page_id: Optional[int]
    :vartype uid: str
    :vartype rotated_angle: float
    :vartype title: str
    """
    def __init__(self, page_id: Optional[int], uid: Optional[str] = None, rotated_angle: float = 0.0, title: str = "") -> None:
        """
        :param page_id: number of the page where table starts
        :param uid: unique identifier of the table
        :param rotated_angle: rotation angle by which the table was rotated during recognition
        :param title: table's title
        """
        import uuid

        self.page_id: Optional[int] = page_id
        self.uid: str = str(uuid.uuid4()) if not uid else uid
        self.rotated_angle: float = rotated_angle
        self.title: str = title

    def to_api_schema(self) -> ApiTableMetadata:
        return ApiTableMetadata(uid=self.uid, page_id=self.page_id, rotated_angle=self.rotated_angle, title=self.title)
