import os
from typing import Optional, Tuple, List
import numpy as np

from dedoc.readers.pdf_reader.pdf_txtlayer_reader.extractor_pdf_textlayer import ExtractorPdfTextLayer
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_base_reader import PdfBaseReader, ParametersForParseDoc
from dedoc.train_dataset.train_dataset_utils import save_page_with_bbox
from dedoc.data_structures.bbox import BBox


class PdfTxtlayerReader(PdfBaseReader):
    """
     Class Pdf with text layer extractor.
     This handler uses a pdfminer library for content extraction.
     For using this class you need set a parameter pdf_with_text_layer=['true', 'auto'].
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.extractor_layer = ExtractorPdfTextLayer(config=config)

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        return extension.lower().endswith("pdf") and (str(parameters.get("pdf_with_text_layer", "false")).lower() == "true")

    def _process_one_page(self,
                          image: np.ndarray,
                          parameters: ParametersForParseDoc,
                          page_number: int,
                          path: str) -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment]]:
        gray_image = self._convert_to_gray(image)
        if parameters.need_pdf_table_analysis:
            cleaned_image, tables = self.table_recognizer. \
                recognize_tables_from_image(image=gray_image,
                                            page_number=page_number,
                                            language=parameters.language,
                                            orient_analysis_cells=parameters.orient_analysis_cells,
                                            orient_cell_angle=parameters.orient_cell_angle,
                                            table_type=parameters.table_type)
        else:
            tables = []

        is_one_column_document_list = None if parameters.is_one_column_document_list is None \
            else parameters.is_one_column_document_list[page_number]

        page = self.extractor_layer.extract_text_layer(path=path,
                                                       page_number=page_number,
                                                       is_one_column_document=is_one_column_document_list)
        if page is None:
            return [], [], []
        unreadable_blocks = [location.bbox for table in tables for location in table.locations]
        page.bboxes = [bbox for bbox in page.bboxes if not self._inside_any_unreadable_block(bbox.bbox, unreadable_blocks)]
        lines = self.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page, call_classifier=False)

        if self.config.get("labeling_mode"):
            save_page_with_bbox(page=page, config=self.config, document_name=os.path.basename(path))

        return lines, tables, page.attachments

    def _inside_any_unreadable_block(self, obj_bbox: BBox, unreadable_blocks: List[BBox]) -> bool:
        """
        Check obj_bbox inside some unreadable blocks or not
        :param obj_bbox: ["x_top_left", "y_top_left", "width", "height"]
        :param unreadable_blocks: List["x_top_left", "y_top_left", "width", "height"]
        :return: Boolean
        """
        for block in unreadable_blocks:
            if block.have_intersection_with_box(obj_bbox):
                return True
        return False
