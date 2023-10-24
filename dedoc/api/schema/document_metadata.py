from typing import Optional

from pydantic import BaseModel, Extra, Field


class DocumentMetadata(BaseModel):
    """
    Document metadata like its name, size, author, etc.
    """
    class Config:
        extra = Extra.allow

    uid: str = Field(description="Document unique identifier (useful for attached files)", example="doc_uid_auto_ba73d76a-326a-11ec-8092-417272234cb0")
    file_name: str = Field(description="Original document name before rename and conversion", example="example.odt")
    temporary_file_name: str = Field(description="File name during parsing (unique name after rename and conversion)", example="123.odt")
    size: int = Field(description="File size in bytes", example=20060)
    modified_time: int = Field(description="Modification time of the document in the UnixTime format", example=1590579805)
    created_time: int = Field(description="Creation time of the document in the UnixTime format", example=1590579805)
    access_time: int = Field(description="File access time in the UnixTime format", example=1590579805)
    file_type: str = Field(description="Mime type of the file", example="application/vnd.oasis.opendocument.text")
    other_fields: Optional[dict] = Field(description="Other optional fields")
