from dataclasses import dataclass

from tdm.datamodel.nodes import FileNode, FileNodeMetadata


@dataclass(frozen=True)
class FileMetadata(FileNodeMetadata):
    extension: str | None = None
    mime: str | None = None
    need_parse: bool = False
    orig_file_ref: FileNode | None = None

    modified_time: int | None = None
    created_time: int | None = None
    access_time: int | None = None
