from typing import Any, Dict, Iterator, Optional

from base_dedoc_file_loader import BaseDedocFileLoader
from langchain_core.documents import Document


class DedocAPIFileLoader(BaseDedocFileLoader):
    """
    This loader allows you to use almost all the functionality of the Dedoc library via dedoc API.
    More information is available at the link:
    https://dedoc.readthedocs.io/en/latest/?badge=latest
    """
    def __init__(  # noqa: FOL005
        self,
        file_path: str,
        url: str = "http://0.0.0.0:1231",
        split: Optional[str] = "document",
        **kwargs: dict
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
            kwargs: Parameters used for document parsing via dedoc API.
                Available parameters:
                    pdf_with_text_layer: This option is used for choosing a specific reader of PDF documents
                    language: Language of the document without a textual layer
                    pages: If you need to read a part of the PDF document, you can use page slice to define the reading range
                    is_one_column_document: Sets the number of columns if the PDF document is without a textual layer in case it’s known beforehand
                    document_orientation: This option is used to control document orientation analysis for PDF documents without a textual layer
                    need_header_footer_analysis: This option is used to remove headers and footers of PDF documents from the output result
                    need_binarization: This option is used to clean background (binarize) for pages of PDF documents without a textual layer
                    More info available at the link:
                            https://dedoc.readthedocs.io/en/latest/dedoc_api_usage/api.html#api-parameters-description
        """
        self.file_path = file_path
        self.url = url
        self.split = split
        self.parsing_params = {**kwargs, **{"structure_type": "tree" if self.split == "node" else "linear"}}

        # protect important parameters
        self.parsing_params["need_pdf_table_analysis"] = "false"
        self.parsing_params["with_attachments"] = "false"
        self.parsing_params["need_content_analysis"] = "false"
        self.parsing_params["document_type"] = "other"
        self.parsing_params["structure_type"] = "linear" if self.split in ["line", "page", "document"] else "tree"
        self.parsing_params["handle_invisible_table"] = "false"
        self.parsing_params["return_format"] = "json"

    def send_file(  # noqa FOL005
        self,
        url: str,
        file_path: str,
        parameters: dict
    ) -> Dict[str, Any]:
        import os
        import json
        try:
            import requests
        except ImportError:
            raise ImportError(
                "`requests` package not found, please install it with `pip install requests`"
            )

        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post(f"{url}/upload", files=files, data=parameters)
            assert r.status_code == 200
            result = json.loads(r.content.decode())
            return result

    def lazy_load(  # noqa: FOL005
        self,
    ) -> Iterator[Document]:
        """Lazily load documents."""
        doc_tree = self.send_file(url=self.url, file_path=self.file_path, parameters=self.parsing_params)
        yield from self.split_document(document_tree=doc_tree, split=self.split)
