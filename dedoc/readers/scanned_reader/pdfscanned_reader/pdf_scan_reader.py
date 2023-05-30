import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional

import cv2
import numpy as np

from dedoc.config import get_config
from dedoc.extensions import recognized_mimes, recognized_extensions
from dedoc.readers.scanned_reader.adaptive_binarizer import AdaptiveBinarizer
from dedoc.readers.scanned_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.scanned_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.scanned_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.scanned_reader.pdf_base_reader import PdfBase, ParametersForParseDoc
from dedoc.readers.scanned_reader.pdfscanned_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier
from dedoc.readers.scanned_reader.pdfscanned_reader.ocr.ocr_line_extractor import OCRLineExtractor
from dedoc.readers.scanned_reader.pdfscanned_reader.scan_rotator import ScanRotator
from dedoc.train_dataset.train_dataset_utils import save_page_with_bbox
from dedoc.utils import supported_image_types


class PdfScanReader(PdfBase):
    """
    This class allows extract content from the .pdf documents without a textual layer (not copyable documents),
    as well as from images (scanned documents).
    """
    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the reader, e.g. logger for logging
        """
        super().__init__(config=config)
        self.scan_rotator = ScanRotator(config=config)
        checkpoint_path = get_config()["resources_path"]
        self.orientation_classifier = ColumnsOrientationClassifier(on_gpu=False,
                                                                   checkpoint_path=checkpoint_path,
                                                                   config=config,
                                                                   delete_lines=False)
        self.binarizer = AdaptiveBinarizer()
        self.ocr = OCRLineExtractor(config=config)
        self.logger = config.get("logger", logging.getLogger())
        if self.config.get("debug_mode") and not os.path.exists(self.config["path_debug"]):
            os.makedirs(self.config["path_debug"])

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader, i.e. it has .pdf extension, or it is an image.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return mime in recognized_mimes.pdf_like_format or mime in recognized_mimes.image_like_format or \
            path.lower().endswith(tuple(recognized_extensions.image_like_format)) or extension.lower().replace(".", "") in supported_image_types

    def _process_one_page(self,
                          image: np.ndarray,
                          parameters: ParametersForParseDoc,
                          page_number: int,
                          path: str) -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment]]:
        #  --- Step 1: correct orientation and detect column count ---
        angle = 0
        columns = None
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
        if columns is not None:
            self.logger.info(f"Final number of columns: {columns}")
        else:
            self.logger.info("Final number of columns: not detected")

        rotated_image, _ = self.scan_rotator.auto_rotate(image, angle)
        if self.config.get("debug_mode"):
            self.logger.info(self.config["path_debug"])
            cv2.imwrite(os.path.join(self.config["path_debug"], f"{datetime.now().strftime('%H-%M-%S')}_result_orientation.jpg"), rotated_image)

        if parameters.need_binarization:
            rotated_image = self.binarizer.binarize(rotated_image)
            if self.config.get("debug_mode"):
                cv2.imwrite(os.path.join(self.config["path_debug"], f"{datetime.now().strftime('%H-%M-%S')}_result_binarization.jpg"), rotated_image)

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

    def _detect_classifier_columns_orientation(self, image: np.ndarray) -> Tuple[int, int]:
        columns_predict, angle_predict = self.orientation_classifier.predict(image)
        self.logger.debug("Predict {}".format(angle_predict))
        return columns_predict, angle_predict
