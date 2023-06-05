import json
import logging
import cv2
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional
import os

from dedoc.train_dataset.data_path_config import table_path as save_path
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.data_classes.tables.table_type import TableTypeAdditionalOptions
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.multipage_table_extractor import MultiPageTableExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.onepage_table_extractor import OnePageTableExtractor

'''-------------------------------------entry class of Table Recognizer Module---------------------------------------'''


class TableRecognizer(object):
    def __init__(self,
                 *,
                 config: dict = None) -> None:

        self.logger = config.get("logger", logging.getLogger(__name__))

        self.onepage_tables_extractor = OnePageTableExtractor(config=config, logger=self.logger)
        self.multipage_tables_extractor = MultiPageTableExtractor(config=config, logger=self.logger)
        self.config = config
        self.table_type = TableTypeAdditionalOptions()
        if config.get("debug", False):
            if not os.path.exists(self.config["path_cells"]):
                os.makedirs(self.config["path_cells"])
            if not os.path.exists(self.config["path_detect"]):
                os.makedirs(self.config["path_detect"])

    def convert_to_multipages_tables(self,
                                     all_single_tables: List[ScanTable],
                                     lines_with_meta: List[LineWithMeta]) -> List[ScanTable]:

        multipage_tables = self.multipage_tables_extractor.extract_multipage_tables(single_tables=all_single_tables,
                                                                                    lines_with_meta=lines_with_meta)
        return multipage_tables

    def recognize_tables_from_image(self,
                                    image: np.ndarray,
                                    page_number: int,
                                    language: str,
                                    orient_analysis_cells: bool,
                                    orient_cell_angle: int,
                                    table_type: str = "") -> Tuple[np.ndarray, List[ScanTable]]:
        self.logger.debug("Page %i" % page_number)
        try:
            cleaned_image, matrix_tables = self.__rec_tables_from_img(image, page_num=page_number,
                                                                      language=language,
                                                                      orient_analysis_cells=orient_analysis_cells,
                                                                      orient_cell_angle=orient_cell_angle,
                                                                      table_type=table_type)
            return cleaned_image, matrix_tables
        except Exception as ex:
            logging.warning(ex)
            if self.config.get("debug_mode", False):
                raise ex
            return image, []

    def __rec_tables_from_img(self,
                              src_image: np.ndarray,
                              page_num: int,
                              language: str,
                              orient_analysis_cells: bool,
                              orient_cell_angle: int,
                              table_type: str) -> Tuple[np.ndarray, List[ScanTable]]:
        gray_image = cv2.cvtColor(src_image, cv2.COLOR_BGR2GRAY) if len(src_image.shape) == 3 else src_image

        single_page_tables = self.onepage_tables_extractor.extract_onepage_tables_from_image(
            image=gray_image,
            page_number=page_num,
            language=language,
            orient_analysis_cells=orient_analysis_cells,
            orient_cell_angle=orient_cell_angle,
            table_type=table_type)
        if self.config.get("labeling_mode", False):
            self.__save_tables(tables=single_page_tables, image=src_image, table_path=save_path)
        if self.table_type.detect_one_cell_table in table_type:
            filtered_tables = single_page_tables
        else:
            filtered_tables = self.__filter_bad_tables(tables=single_page_tables, image=gray_image)

        cleaned_image = self.__clean_image_from_table(image=src_image, tables=filtered_tables)

        return cleaned_image, filtered_tables

    @staticmethod
    def __clean_image_from_table(image: np.ndarray, tables: List[ScanTable]) -> np.ndarray:
        image_copy = np.copy(image)
        for table in tables:
            for location in table.locations:
                image_copy = TableRecognizer.__clean_image(image_copy, location.bbox)
        return image_copy

    @staticmethod
    def __clean_image(image: np.ndarray, bbox: BBox, color: int = 255) -> np.ndarray:
        """
        replace bboxes with given color (for example to remove tables from images)
        @param image: original image
        @param bbox: bbox to clear from image
        @param color: color to replace bboxes
        @return: image without given bboxes
        """
        x_min = bbox.x_top_left
        x_max = x_min + bbox.width

        y_min = bbox.y_top_left
        y_max = y_min + bbox.height

        if len(image.shape) == 3:
            image[y_min: y_max, x_min: x_max, :] = color
        else:
            image[y_min: y_max, x_min: x_max] = color

        return image

    def __filter_bad_tables(self, tables: List[ScanTable], image: np.ndarray) -> List[ScanTable]:
        filtered = []
        for table in tables:
            if not self.__if_not_table(table, image):
                filtered.append(table)
        return filtered

    def __if_not_table(self, table: ScanTable, image: np.ndarray) -> bool:
        bbox = table.location.bbox
        height, width = image.shape
        table_image = image[max(bbox.y_top_left, 0): min(bbox.y_bottom_right, height),
                            max(bbox.x_top_left, 0): min(bbox.x_bottom_right, width)]
        mean = table_image.mean()
        std = table_image.std()
        white_mean = (table_image > 225).mean()
        black_mean = (table_image < 225).mean()
        table_area = bbox.width * bbox.height
        cells_area = 0
        for row in table.matrix_cells:
            for cell in row:
                cells_area += cell.width * cell.height

        ratio = cells_area / table_area
        res = ((white_mean < 0.5) or
               (black_mean > 0.3) or
               (std < 30) or (mean < 150) or
               (mean < 200 and std < 80) or
               ratio < 0.65)
        return res

    def __save_tables(self, tables: List[ScanTable], image: np.ndarray, table_path: Optional[str] = None) -> None:
        image = Image.fromarray(image)
        os.makedirs(table_path, exist_ok=True)
        for table in tables:
            images_cnt = len(os.listdir(table_path))
            image_path = os.path.join(table_path, "{:06d}.png".format(images_cnt))
            jsons_path = os.path.join(table_path, "{:06d}.json".format(images_cnt))
            image.save(image_path)
            with open(jsons_path, "w") as out:
                json.dump(obj=table.to_dict(), fp=out, indent=4, ensure_ascii=False)
