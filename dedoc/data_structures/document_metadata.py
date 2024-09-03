from typing import Dict, Optional, Union

from dedoc.api.schema.document_metadata import DocumentMetadata as ApiDocumentMetadata
from dedoc.data_structures.serializable import Serializable


class DocumentMetadata(Serializable):
    """
    This class holds information about document metadata.

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

    def __init__(self,
                 file_name: str,
                 temporary_file_name: str,
                 size: int,
                 modified_time: int,
                 created_time: int,
                 access_time: int,
                 file_type: str,
                 uid: Optional[str] = None,
                 **kwargs: Dict[str, Union[str, int, float]]) -> None:
        """
        :param uid: document unique identifier
        :param file_name: original document name
        :param temporary_file_name: file name during parsing
        :param size: size of the original file in bytes
        :param modified_time: time of the last modification in unix time format
        :param created_time: time of the creation in unixtime
        :param access_time: time of the last access to the file in unixtime
        :param file_type: mime type of the file
        """
        import uuid

        self.file_name: str = file_name
        self.temporary_file_name: str = temporary_file_name
        self.size: int = size
        self.modified_time: int = modified_time
        self.created_time: int = created_time
        self.access_time: int = access_time
        self.file_type: str = file_type
        for key, value in kwargs.items():
            self.add_attribute(key, value)
        self.uid: str = f"doc_uid_auto_{uuid.uuid1()}" if uid is None else uid

    def add_attribute(self, key: str, value: Union[str, int, float]) -> None:
        setattr(self, key, value)

    def to_api_schema(self) -> ApiDocumentMetadata:
        return ApiDocumentMetadata(**vars(self))
