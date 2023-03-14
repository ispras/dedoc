import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional

import cv2
import numpy as np

from dedoc.extensions import recognized_mimes, recognized_extensions
from dedoc.readers.scanned_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.scanned_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.scanned_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.scanned_reader.pdf_base_reader import PdfBase, ParametersForParseDoc
from dedoc.readers.scanned_reader.pdfscanned_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier
from dedoc.readers.scanned_reader.pdfscanned_reader.ocr.ocr_line_extractor import OCRLineExtractor
from dedoc.readers.scanned_reader.pdfscanned_reader.scan_rotator import ScanRotator
from dedoc.train_dataset.train_dataset_utils import save_page_with_bbox
from dedoc.utils.image_utils import supported_image_types


class PdfScanReader(PdfBase):
    """
     Class Pdf без текстового слоя (сканы)
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.scan_rotator = ScanRotator(config=config)
        checkpoint_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../resources/"))
        self.orientation_classifier = ColumnsOrientationClassifier(on_gpu=False,
                                                                   checkpoint_path=checkpoint_path,
                                                                   config=config,
                                                                   delete_lines=False)
        # TODO add adaptive binarization
        self.ocr = OCRLineExtractor(config=config)
        self.logger = config.get("logger", logging.getLogger())

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: str,
                 parameters: Optional[dict] = None) -> bool:
        parameters = {} if parameters is None else parameters
        with_archive = parameters.get("archive_as_single_file", "true").lower() == "true"
        return self.__check_mime(mime, with_archive) or self.__check_path(path, with_archive) or \
            extension.lower().replace(".", "") in supported_image_types

    def _process_one_page(self,
                          image: np.ndarray,
                          parameters: ParametersForParseDoc,
                          page_number: int,
                          path: str) -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment]]:
        #  --- Step 1: correct orientation and detect column count ---
        angle = 0
        if parameters.is_one_column_document is None or parameters.document_orientation is None:
            self.logger.info("Call orientation and columns classifier")
            columns, angle = self._detect_classifier_columns_orientation(image)

        if parameters.is_one_column_document is not None:
            is_one_column_document = parameters.is_one_column_document
        else:
            is_one_column_document = True if columns == 1 else False

        if parameters.document_orientation is True:
            angle = 0

        self.logger.info(f"Final orientation angle: {angle}")
        self.logger.info(f"Final number of columns: {columns}")
        rotated_image, _ = self.scan_rotator.auto_rotate(image, angle)

        if self.config.get("debug_mode"):
            time = datetime.now().strftime("%H-%M-%S")
            cv2.imwrite(os.path.join(self.config["path_debug"], f"{time}_result_orientation.jpg"), rotated_image)

        #  --- Step 2: table detection and recognition ---
        if parameters.need_pdf_table_analysis:
            clean_image, tables = self.table_recognizer. \
                recognize_tables_from_image(image=rotated_image,
                                            page_number=page_number,
                                            language=parameters.language,
                                            orient_analysis_cells=parameters.orient_analysis_cells,
                                            orient_cell_angle=parameters.orient_cell_angle,
                                            table_type=parameters.table_type)
        else:
            clean_image, tables = rotated_image, []

        # --- Step 3: plain text recognition and text style detection ---
        page = self.ocr.split_image2lines(image=clean_image,
                                          language=parameters.language,
                                          is_one_column_document=is_one_column_document,
                                          page_num=page_number)

        lines = self.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page)
        if self.config.get("labeling_mode"):
            save_page_with_bbox(page=page, config=self.config, document_name=os.path.basename(path))

        return lines, tables, page.attachments

    @staticmethod
    def __check_mime(mime: str, with_archive: bool) -> bool:
        return (mime in recognized_mimes.pdf_like_format or
                (mime in recognized_mimes.archive_like_format and with_archive) or
                mime in recognized_mimes.image_like_format)

    def __check_path(self, path: str, with_archive: bool) -> bool:
        return (path.lower().endswith(tuple(recognized_extensions.image_like_format)) or
                (path.lower().endswith(tuple(recognized_extensions.archive_like_format)) and with_archive))

    def _detect_classifier_columns_orientation(self, image: np.ndarray) -> Tuple[int, int]:
        columns_predict, angle_predict = self.orientation_classifier.predict(image)
        self.logger.debug("Predict {}".format(angle_predict))
        return columns_predict, angle_predict
