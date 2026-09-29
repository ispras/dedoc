from dataclasses import dataclass

from dedocutils.data_structures import BBox
from tdm.abstract.datamodel import BaseNodeMetadata

from dedoc_future.datamodel.nodes.page import PageNode


@dataclass(frozen=True, kw_only=True)
class PageObjectMetadata(BaseNodeMetadata):
    page_ref: PageNode
    bbox: BBox
    caption: str | None = None
