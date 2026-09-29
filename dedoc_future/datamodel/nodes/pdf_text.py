from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractContentNode

from dedoc_future.datamodel.metadata.pdf_text import PdfTextMetadata


@dataclass(frozen=True)
class PdfTextNode(AbstractContentNode[PdfTextMetadata, str]):
    """
    Node for pdf text representation.
    ``content`` contains node text.
    """
    pass
