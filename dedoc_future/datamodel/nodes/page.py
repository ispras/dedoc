from abc import ABCMeta
from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNode
from tdm.wrapper.node import AbstractNodeWrapper, generate_wrapper

from dedoc_future.datamodel.markup.pdf_page import AbstractPdfPageMarkup, PdfPageMarkup
from dedoc_future.datamodel.metadata.page import PageMetadata


@dataclass(frozen=True)
class PageNode(AbstractNode[PageMetadata]):
    pass


@generate_wrapper(PdfPageMarkup)
class PageNodeWrapper(PageNode, AbstractPdfPageMarkup, AbstractNodeWrapper[PageNode], metaclass=ABCMeta):
    pass
