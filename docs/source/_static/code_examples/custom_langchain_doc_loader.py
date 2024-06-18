from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Dict,
    Generator,
    Iterator,
    List,
    Optional
)

if TYPE_CHECKING:
    from dedoc.data_structures import TreeNode

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from dedoc.data_structures import TreeNode


class BaseDedocParser(ABC):
    @abstractmethod
    def lazy_parse(self,  # noqa: FOL005
                   obj: str,
                   parsing_parameters: Optional[Dict[str, str]] = None,
                   split: Optional[str] = "document"
                   ) -> Iterator[Document]:
        pass

    def parse(self,  # noqa: FOL005
              obj: str,
              parsing_parameters: Optional[Dict[str, str]] = None,
              split: Optional[str] = "document"
              ) -> List[Document]:
        return list(self.lazy_parse(obj, parsing_parameters, split))


class DedocParser(BaseDedocParser):
    def __init__(self,  # noqa: FOL005
                 manager_config: Optional[dict] = None,
                 ) -> None:
        self.manager_config = manager_config
        from dedoc import DedocManager
        self.dedoc_manager = DedocManager(manager_config=self.manager_config)

    def parse_subparagraphs(self,  # noqa: FOL005
                            doc_tree: TreeNode,
                            doc_metadata: dict
                            ) -> Generator:
        if len(doc_tree.subparagraphs) > 0:
            for subparagraph in doc_tree.subparagraphs:
                yield from self.parse_subparagraphs(doc_tree=subparagraph, doc_metadata=doc_metadata)
        else:
            yield Document(page_content=doc_tree.text, metadata={**doc_metadata, **vars(doc_tree.metadata)})

    def lazy_parse(self,  # noqa: FOL005
                   obj: str,
                   parsing_parameters: Optional[Dict[str, str]] = None,
                   split: Optional[str] = "document"
                   ) -> Iterator[Document]:
        from dedoc.api.api_utils import json2txt

        document_tree = self.dedoc_manager.parse(obj, parameters=parsing_parameters)
        if split == "document":
            text = json2txt(paragraph=document_tree.content.structure)
            yield Document(page_content=text, metadata=vars(document_tree.metadata))
        elif split == "page":
            initial_page_id = document_tree.content.structure.subparagraphs[0].metadata.page_id
            initial_page_text = ""
            initial_page_metadata = vars(document_tree.metadata)
            for node_index, node in enumerate(document_tree.content.structure.subparagraphs):
                if node.metadata.page_id == initial_page_id:
                    initial_page_text += json2txt(node)
                    initial_page_metadata["page_id"] = initial_page_id
                    if node_index == len(document_tree.content.structure.subparagraphs) - 1:
                        yield Document(page_content=initial_page_text, metadata=dict(initial_page_metadata))
                else:
                    yield Document(page_content=initial_page_text, metadata=dict(initial_page_metadata))
                    initial_page_id = node.metadata.page_id
                    initial_page_text = json2txt(node)
                    initial_page_metadata["page_id"] = initial_page_id
        elif split == "line":
            initial_document_metadata = vars(document_tree.metadata)
            for node in document_tree.content.structure.subparagraphs:
                line_metadata = node.metadata
                yield Document(page_content=json2txt(node), metadata={**initial_document_metadata, **vars(line_metadata)})
        elif split == "node":
            yield from self.parse_subparagraphs(doc_tree=document_tree.content.structure, doc_metadata=vars(document_tree.metadata))


class DedocLoader(BaseLoader):
    def __init__(  # noqa: FOL005
        self,
        file_path: str,
        split: Optional[str] = "document",
        **kwargs
    ) -> None:
        """Initialize with file path
        Args:
            file_path: Path to the file for processing
            split: Controls how the document is divided when being processed
                "document": In this mode, the entire text of the document is returned at once
                "line": In this mode, all text lines of the document are returned one by one
                "page": In this mode, the contents of the document pages are returned one by one
                "node": In this mode, the text contents of the document tree nodes are returned one by one
                        More info available at: https://dedoc.readthedocs.io/en/latest/structure_types/other.html
            kwargs: Parameters used for document parsing via dedoc.
                Available parameters:
                    pdf_with_text_layer: This option is used for choosing a specific reader of PDF documents
                    language: Language of the document without a textual layer
                    pages: If you need to read a part of the PDF document, you can use page slice to define the reading range
                    is_one_column_document: This option is used to set the number of columns if the PDF document is without a textual layer in case it’s known beforehand
                    document_orientation: This option is used to control document orientation analysis for PDF documents without a textual layer
                    need_header_footer_analysis: This option is used to remove headers and footers of PDF documents from the output result
                    need_binarization: This option is used to clean background (binarize) for pages of PDF documents without a textual layer
                    More info available at the link:
                            https://dedoc.readthedocs.io/en/latest/parameters/parameters.html
        """
        self.file_path = file_path
        self.split = split
        self.parsing_params = {**kwargs, **{"structure_type": "tree" if self.split == "node" else "linear"}}
        try:
            from dedoc.utils.langchain_manager_config import make_manager_config
        except ImportError:
            raise ImportError(
                "`dedoc` package not found, please install it with `pip install dedoc`"
            )
        self.parser = DedocParser(manager_config=make_manager_config(file_path=self.file_path, parsing_params=self.parsing_params, split=self.split))

    def lazy_load(  # noqa: FOL005
        self,
    ) -> Iterator[Document]:
        """Lazily load documents."""
        yield from self.parser.parse(self.file_path, parsing_parameters=self.parsing_params, split=self.split)
