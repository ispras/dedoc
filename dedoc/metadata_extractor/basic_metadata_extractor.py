import os
from typing import Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.utils import get_file_mime_type


class BasicMetadataExtractor:

    def add_metadata(self,
                     doc: Optional[DocumentContent],
                     directory: str,
                     filename: str,
                     original_filename: str,
                     parameters: dict = None) -> ParsedDocument:
        if parameters is None:
            parameters = {}
        meta_info = self._get_base_meta_information(directory, filename, original_filename, parameters)
        metadata = DocumentMetadata(
            file_name=meta_info["file_name"],
            file_type=meta_info["file_type"],
            size=meta_info["size"],
            access_time=meta_info["access_time"],
            created_time=meta_info["created_time"],
            modified_time=meta_info["modified_time"]
        )
        parsed_document = ParsedDocument(metadata=metadata, content=doc)
        return parsed_document

    def _get_base_meta_information(self, dir: str, filename: str, name_actual: str, parameters: dict) -> dict:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(os.path.join(dir, filename))
        meta = {
            "file_name": name_actual,
            "file_type": get_file_mime_type(os.path.join(dir, filename)),
            "size": size,  # in bytes
            "access_time": atime,
            "created_time": ctime,
            "modified_time": mtime
        }

        return meta
