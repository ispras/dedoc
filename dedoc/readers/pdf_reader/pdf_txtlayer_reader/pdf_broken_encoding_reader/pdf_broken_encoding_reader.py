import logging
from collections import namedtuple
from typing import List, Optional, Tuple

from numpy import ndarray

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_base_reader import ParametersForParseDoc
from dedoc.readers.pdf_reader.pdf_base_reader import PdfBaseReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.pdf_worker.pdf_reader import PDFReader

logging.getLogger("pdfminer").setLevel(logging.ERROR)
WordObj = namedtuple("Word", ["start", "end", "value"])


class PdfBrokenEncodingReader(PdfBaseReader):
    """
    This class allows to extract text from the .pdf documents with a textual layer with broken encoding
    (copyable documents, but copied text is incorrect) with complex background.
    It uses a pdfminer library for text extraction and CNN for font's glyphs prediction.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes

        super().__init__(config=config, recognized_extensions=recognized_extensions.pdf_like_format, recognized_mimes=recognized_mimes.pdf_like_format)

        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdfminer_reader.pdfminer_extractor import PdfminerExtractor
        self.extractor_layer = PdfminerExtractor(config=self.config)
        self.__pdf_txtlayer_reader = PdfTxtlayerReader(config=config)
        self.reader = PDFReader()

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader (PDF format is supported only).
        This method returns `True` only when the key `pdf_with_text_layer` with value `bad_encoding_reader` is set in the dictionary `parameters`.

        You can look to :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer

        return super().can_read(file_path=file_path, mime=mime, extension=extension) and get_param_pdf_with_txt_layer(
            parameters) == "bad_encoding_reader"

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines
        """
        import dedoc.utils.parameter_utils as param_utils
        parameters = {} if parameters is None else parameters
        first_page, last_page = param_utils.get_param_page_slice(parameters)
        params_for_parse = ParametersForParseDoc(
            language=param_utils.get_param_language(parameters),
            is_one_column_document=param_utils.get_param_is_one_column_document(parameters),
            document_orientation=param_utils.get_param_document_orientation(parameters),
            need_header_footers_analysis=param_utils.get_param_need_header_footers_analysis(parameters),
            need_pdf_table_analysis=param_utils.get_param_need_pdf_table_analysis(parameters),
            first_page=first_page,
            last_page=last_page,
            need_binarization=param_utils.get_param_need_binarization(parameters),
            table_type=param_utils.get_param_table_type(parameters),
            with_attachments=param_utils.get_param_with_attachments(parameters),
            attachments_dir=param_utils.get_param_attachments_dir(parameters, file_path),
            need_content_analysis=param_utils.get_param_need_content_analysis(parameters),
            need_gost_frame_analysis=param_utils.get_param_need_gost_frame_analysis(parameters),
            pdf_with_txt_layer=param_utils.get_param_pdf_with_txt_layer(parameters)
        )
        pages, layouts = self.reader.get_correct_layout(file_path)
        lines = []
        for idx, (page, layout) in enumerate(zip(pages, layouts)):
            page_bb = self.extractor_layer.handle_page(page, idx, file_path, params_for_parse, layout)
            page_bb.bboxes = [bbox for bbox in page_bb.bboxes]
            lines += self.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page_bb, call_classifier=False)

        return UnstructuredDocument(tables=[], lines=lines, attachments=[])

    def _process_one_page(self,
                          image: ndarray,
                          parameters: ParametersForParseDoc,
                          page_number: int,
                          path: str) -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment], List[float]]:
        if parameters.need_pdf_table_analysis:
            gray_image = self._convert_to_gray(image)
            cleaned_image, tables = self.table_recognizer.recognize_tables_from_image(
                image=gray_image,
                page_number=page_number,
                language=parameters.language,
                table_type=parameters.table_type
            )

        layout = self.reader.get_correct_layout(path)

        lines = []
        for idx, page in enumerate(layout):
            page_bb = self.extractor_layer.handle_page(page, idx, path, parameters)
            page_bb.bboxes = [bbox for bbox in page_bb.bboxes]
            lines.append(self.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page_bb,
                                                                                      call_classifier=False))
        return lines, [], [], []
