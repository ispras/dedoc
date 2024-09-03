from typing import Optional

from pydantic import BaseModel, Field


class TableMetadata(BaseModel):
    """
    Holds the information about table unique identifier, rotation angle (if table has been rotated - for images) and so on.

    :ivar page_id: number of the page where table starts
    :ivar uid: unique identifier of the table (used for linking table to text)
    :ivar rotated_angle: value of the rotation angle by which the table was rotated during recognition
    :ivar title: table's title

    :vartype page_id: Optional[int]
    :vartype uid: str
    :vartype rotated_angle: float
    :vartype title: str
    """
    page_id: Optional[int] = Field(description="Number of the page where the table starts", example=0)
    uid: str = Field(description="Unique identifier of the table", example="e8ba5523-8546-4804-898c-2f4835a1804f")
    rotated_angle: float = Field(description="Value of the rotation angle (in degrees) by which the table was rotated during recognition", example=1.0)
    title: str = Field(description="Table's title")
