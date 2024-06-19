from typing import Iterator, Optional

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


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
                    is_one_column_document: Sets the number of columns if the PDF document is without a textual layer in case it’s known beforehand
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
            from dedoc import DedocManager
            from dedoc.utils.langchain import make_manager_config
        except ImportError:
            raise ImportError(
                "`dedoc` package not found, please install it with `pip install dedoc`"
            )
        self.dedoc_manager = DedocManager(manager_config=make_manager_config(file_path=self.file_path, parsing_params=self.parsing_params, split=self.split))

    def lazy_load(  # noqa: FOL005
        self,
    ) -> Iterator[Document]:
        """Lazily load documents."""
        from dedoc.utils.langchain import split_document

        doc_tree = self.dedoc_manager.parse(self.file_path, parameters=self.parsing_parameters)
        document_generator = split_document(document_tree=doc_tree, split=self.split)
        for document in document_generator:
            yield Document(page_content=document.page_content, metadata=document.metadata)
