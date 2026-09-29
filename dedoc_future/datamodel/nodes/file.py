from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractContentNode

from dedoc_future.datamodel.metadata.file import FileMetadata


@dataclass(frozen=True)
class FileNode(AbstractContentNode[FileMetadata, str]):
    """
    Node for file representation.
    ``content`` contains file path.
    """
    pass
