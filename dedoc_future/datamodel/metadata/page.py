from dataclasses import dataclass

from tdm.abstract.datamodel import BaseNodeMetadata
from tdm.datamodel.nodes import FileNode


@dataclass(frozen=True, kw_only=True)
class PageMetadata(BaseNodeMetadata):
    number: int
    file_ref: FileNode
