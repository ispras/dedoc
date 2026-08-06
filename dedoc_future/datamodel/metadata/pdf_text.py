from dataclasses import dataclass

from tdm.datamodel.nodes import TextNodeMetadata

from dedoc_future.datamodel.metadata.page_object import PageObjectMetadata


@dataclass(frozen=True)
class PdfTextMetadata(TextNodeMetadata, PageObjectMetadata):
    pass
