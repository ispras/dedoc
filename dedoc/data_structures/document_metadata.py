import uuid
from typing import Any, Dict, Union

from dedoc.api.schema.document_metadata import DocumentMetadata as ApiDocumentMetadata
from dedoc.data_structures.serializable import Serializable


class DocumentMetadata(Serializable):
    """
    This class holds information about document metadata.
    """

    def __init__(self,
                 file_name: str,
                 temporary_file_name: str,
                 size: int,
                 modified_time: int,
                 created_time: int,
                 access_time: int,
                 file_type: str,
                 uid: str = None,
                 **kwargs: Dict[str, Union[str, int, float]]) -> None:
        """
        :param uid: document unique identifier (useful for attached files)
        :param file_name: original document name (before rename and conversion, so it can contain non-ascii symbols, spaces and so on)
        :param temporary_file_name: file name during parsing (unique name after rename and conversion);
        :param size: size of the original file in bytes
        :param modified_time: time of the last modification in unix time format (seconds since the epoch)
        :param created_time: time of the creation in unixtime
        :param access_time: time of the last access to the file in unixtime
        :param file_type: mime type of the file
        """
        self.file_name = file_name
        self.temporary_file_name = temporary_file_name
        self.size = size
        self.modified_time = modified_time
        self.created_time = created_time
        self.access_time = access_time
        self.file_type = file_type
        for key, value in kwargs.items():
            self.add_attribute(key, value)
        self.uid = f"doc_uid_auto_{uuid.uuid1()}" if uid is None else uid

    def add_attribute(self, key: str, value: Any) -> None:  # noqa
        setattr(self, key, value)

    def to_api_schema(self) -> ApiDocumentMetadata:
        return ApiDocumentMetadata(**vars(self))
