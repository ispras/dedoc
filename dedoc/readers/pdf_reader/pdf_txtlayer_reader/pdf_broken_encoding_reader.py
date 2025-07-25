from typing import Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader


class PdfBrokenEncodingReader(PdfTxtlayerReader):
    """
    This class allows to extract content (text, tables, attachments) from the .pdf documents with a textual layer with broken encoding
    (copyable documents, but copied text is incorrect) with complex background.
    It uses a pdfminer library for text extraction and CNN for font's glyphs prediction.
    Currently, only Russian and English languages are supported.

    For more information, look to `pdf_with_text_layer` option description in :ref:`pdf_handling_parameters`.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding.broken_encoding_extractor import BrokenEncodingExtractor

        self.extractor_layer = BrokenEncodingExtractor(config=self.config)
        self.reader_key = "bad_encoding"

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader (PDF format is supported only).
        This method returns `True` only when the key `pdf_with_text_layer` with value `bad_encoding` is set in the dictionary `parameters`.

        You can look to :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return super().can_read(file_path=file_path, mime=mime, extension=extension, parameters=parameters)

    def _postprocess(self, document: UnstructuredDocument) -> UnstructuredDocument:
        """
        Perform document postprocessing.
        """
        self.extractor_layer.cache = {}
        return document
