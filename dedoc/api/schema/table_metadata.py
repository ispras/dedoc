from typing import Optional

from pydantic import BaseModel, Field


class TableMetadata(BaseModel):
    """
    Holds the information about table unique identifier, rotation angle (if table has been rotated - for images) and so on.
    """
    page_id: Optional[int] = Field(description="Number of the page where the table starts", example=0)
    uid: str = Field(description="Unique identifier of the table", example="e8ba5523-8546-4804-898c-2f4835a1804f")
    rotated_angle: float = Field(description="Value of the rotation angle (in degrees) by which the table was rotated during recognition", example=1.0)
