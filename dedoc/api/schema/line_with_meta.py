from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.annotation import Annotation


class LineWithMeta(BaseModel):
    """
    Textual line with text annotations.

    :ivar text: text of the line
    :ivar annotations: text annotations (font, size, bold, italic, etc.)

    :vartype text: str
    :vartype annotations: List[Annotation]
    """
    text: str = Field(description="Text of the line", example="Some text")
    annotations: List[Annotation] = Field(description="Text annotations (font, size, bold, italic, etc.)")
