from pydantic import BaseModel, Extra, Field


class DocumentMetadata(BaseModel):
    """
    Document metadata like its name, size, author, etc.

    :ivar file_name: original document name (before rename and conversion, so it can contain non-ascii symbols, spaces and so on)
    :ivar temporary_file_name: file name during parsing (unique name after rename and conversion)
    :ivar size: size of the original file in bytes
    :ivar modified_time: time of the last modification in unix time format (seconds since the epoch)
    :ivar created_time: time of the creation in unixtime
    :ivar access_time: time of the last access to the file in unixtime
    :ivar file_type: mime type of the file
    :ivar uid: document unique identifier (useful for attached files)

    :vartype file_name: str
    :vartype temporary_file_name: str
    :vartype size: int
    :vartype modified_time: int
    :vartype created_time: int
    :vartype access_time: int
    :vartype file_type: str
    :vartype uid: str

    Additional variables may be added with other file metadata.
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
