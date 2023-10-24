from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.annotation import Annotation


class LineWithMeta(BaseModel):
    """
    Textual line with text annotations.
    """
    text: str = Field(description="Text of the line", example="Some text")
    annotations: List[Annotation] = Field(description="Text annotations (font, size, bold, italic and etc)")
