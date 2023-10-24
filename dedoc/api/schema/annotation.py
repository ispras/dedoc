from pydantic import BaseModel, Field


class Annotation(BaseModel):
    """
    The piece of information about the text line: it's appearance or links to another document object.
    For example Annotation(1, 13, "italic", "True") says that text between 1st and 13th symbol was written in italic.
    """
    start: int = Field(description="Start of the annotated text", example=0)
    end: int = Field(description="End of the annotated text (end isn't included)", example=5)
    name: str = Field(description="Annotation name", example="italic")
    value: str = Field(description="Annotation value. For example, it may be font size value for size type", example="True")
