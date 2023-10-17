import uuid

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
                 other_fields: dict = None,
                 uid: str = None) -> None:
        """
        :param uid: document unique identifier (useful for attached files)
        :param file_name: original document name (before rename and conversion, so it can contain non-ascii symbols, spaces and so on)
        :param temporary_file_name: file name during parsing (unique name after rename and conversion);
        :param size: size of the original file in bytes
        :param modified_time: time of the last modification in unix time format (seconds since the epoch)
        :param created_time: time of the creation in unixtime
        :param access_time: time of the last access to the file in unixtime
        :param file_type: mime type of the file
        :param other_fields: additional fields of user metadata
        """
        self.file_name = file_name
        self.temporary_file_name = temporary_file_name
        self.size = size
        self.modified_time = modified_time
        self.created_time = created_time
        self.access_time = access_time
        self.file_type = file_type
        self.other_fields = {}
        if other_fields is not None and len(other_fields) > 0:
            self.extend_other_fields(other_fields)
        self.uid = f"doc_uid_auto_{uuid.uuid1()}" if uid is None else uid

    def set_uid(self, uid: str) -> None:
        self.uid = uid  # noqa

    def extend_other_fields(self, new_fields: dict) -> None:
        """
        Add new attributes to the class and to the other_fields dictionary.

        :param new_fields: fields to add
        """
        assert (new_fields is not None)
        assert (len(new_fields) > 0)

        for key, value in new_fields.items():
            setattr(self, key, value)
            self.other_fields[key] = value

    def to_api_schema(self) -> ApiDocumentMetadata:
        api_document_metadata = ApiDocumentMetadata(uid=self.uid, file_name=self.file_name, temporary_file_name=self.temporary_file_name, size=self.size,
                                                    modified_time=self.modified_time, created_time=self.created_time, access_time=self.access_time,
                                                    file_type=self.file_type, other_fields=self.other_fields)
        if self.other_fields is not None:
            for (key, value) in self.other_fields.items():
                setattr(api_document_metadata, key, value)
        return api_document_metadata
