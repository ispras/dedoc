from typing import Optional

from pydantic import BaseModel, Extra, Field


class LineMetadata(BaseModel):
    """
    Holds information about document node/line metadata, such as page number or line type.
    """
    class Config:
        extra = Extra.allow

    paragraph_type: str = Field(description="Type of the document line/paragraph (header, list_item, list) and etc.", example="raw_text")
    page_id: int = Field(description="Page number of the line/paragraph beginning", example=0)
    line_id: Optional[int] = Field(description="Line number", example=1)
    other_fields: Optional[dict] = Field(description="Some other fields")
