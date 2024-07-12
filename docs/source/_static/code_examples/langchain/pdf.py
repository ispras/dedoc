from dedoc_loader import DedocBaseLoader  # noqa from langchain_community.document_loaders.dedoc import DedocBaseLoader


class DedocPDFLoader(DedocBaseLoader):
    """
    Load PDF files using `dedoc`.
    The file loader can automatically detect the correctness of a textual layer in the
        PDF document.
    Note that `__init__` method supports dedoc_kwargs that differ from ones of
        DedocBaseLoader.

    dedoc_kwargs: parameters used for document parsing via `dedoc` (https://dedoc.readthedocs.io/en/latest/parameters/parameters.html).
        with_attachments: enable attached files extraction, you need also
            need_content_analysis parameter to get results
        need_content_analysis: enable attached files parsing, works only when
            with_attachments==True
        recursion_deep_attachments: recursion level for attached files extraction,
            works only when with_attachments==True
        pdf_with_text_layer: type of handler for parsing
        language: language of the document for PDF without a textual layer
        pages: page slice to define the reading range for parsing
        is_one_column_document: number of columns in case it’s known beforehand for PDF
            without a textual layer
        document_orientation: fix document orientation (90, 180, 270 degrees) for PDF
            without a textual layer
        need_header_footer_analysis: remove headers and footers from the output result
        need_binarization: clean pages background (binarize) for PDF without a textual
            layer
        need_pdf_table_analysis: parse tables for PDF without a textual layer

    Examples
    --------
    ```python
    from langchain_community.document_loaders import DedocPDFLoader

    loader = DedocPDFLoader(
        "example.pdf", split="page", pdf_with_text_layer="tabby", pages=":10"
    )
    docs = loader.load()
    ```

    References
    ----------
    https://dedoc.readthedocs.io/en/latest/parameters/pdf_handling.html
    https://dedoc.readthedocs.io/en/latest/modules/readers.html#dedoc.readers.PdfAutoReader
    """

    def _make_config(self) -> dict:
        from dedoc.utils.langchain import make_manager_pdf_config

        return make_manager_pdf_config(
            file_path=self.file_path,
            parsing_params=self.parsing_parameters,
            split=self.split,
        )
