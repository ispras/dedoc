from typing import Optional

from pydantic import BaseModel, Extra, Field


class LineMetadata(BaseModel):
    """
    Holds information about document node/line metadata, such as page number or line type.

    :ivar paragraph_type: type of the document line/paragraph (header, list_item, list, etc.)
    :ivar page_id: page number where paragraph starts, the numeration starts from page 0
    :ivar line_id: line number inside the entire document, the numeration starts from line 0

    :vartype paragraph_type: str
    :vartype page_id: int
    :vartype line_id: Optional[int]

    Additional variables may be added with other line metadata.
    """
    class Config:
        extra = Extra.allow

    paragraph_type: str = Field(description="Type of the document line/paragraph (header, list_item, list, etc.)", example="raw_text")
    page_id: int = Field(description="Page number of the line/paragraph beginning", example=0)
    line_id: Optional[int] = Field(description="Line number", example=1)
