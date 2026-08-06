from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractContentNode

from dedoc_future.datamodel.metadata.pdf_image import PdfImageMetadata


@dataclass(frozen=True)
class PdfImageNode(AbstractContentNode[PdfImageMetadata, str]):
    """
    Node for pdf image representation.
    ``content`` contains image file path.
    """
    pass
