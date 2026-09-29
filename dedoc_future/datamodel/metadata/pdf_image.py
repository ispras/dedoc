from dataclasses import dataclass

from tdm.datamodel.nodes import ImageNodeMetadata

from dedoc_future.datamodel.metadata.page_object import PageObjectMetadata


@dataclass(frozen=True)
class PdfImageMetadata(ImageNodeMetadata, PageObjectMetadata):
    pass
