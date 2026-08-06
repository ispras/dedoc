from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNode

from dedoc_future.datamodel.metadata.page_object import PageObjectMetadata


@dataclass(frozen=True)
class PdfTableNode(AbstractNode[PageObjectMetadata]):
    """
    Node for pdf table representation.
    """
    pass
