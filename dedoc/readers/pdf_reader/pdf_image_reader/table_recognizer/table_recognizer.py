import json
import logging
import os
import time
import traceback
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.data_classes.tables.table_type import TableTypeAdditionalOptions
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.multipage_table_extractor import MultiPageTableExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.onepage_table_extractor import OnePageTableExtractor
from dedoc.utils.image_utils import fill_bbox_on_image

"""-------------------------------------entry class of Table Recognizer Module---------------------------------------"""


class TableRecognizer:
    """
    The class recognizes tables from document images. This class is internal to the system.
    It is called from readers such as :class:`dedoc.readers.PdfTxtlayerReader` or :class:`dedoc.readers.PdfImageReader`.

    * The class recognizes tables with borders from the document image using
      :meth:`~dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer.TableRecognizer.recognize_tables_from_image`;
    * The class also analyzes recognized single-page tables and combines them into multi-page ones using
      :meth:`~dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer.TableRecognizer.convert_to_multipages_tables`
    """

    def __init__(self, *, config: dict = None) -> None:
        self.logger = config.get("logger", logging.getLogger())
        self.onepage_tables_extractor = OnePageTableExtractor(config=config, logger=self.logger)
        self.multipage_tables_extractor = MultiPageTableExtractor(config=config, logger=self.logger)
        self.config = config
        self.table_type = TableTypeAdditionalOptions()

    def convert_to_multipages_tables(self, all_single_tables: List[ScanTable], lines_with_meta: List[LineWithMeta]) -> List[ScanTable]:
        """
        The function analyzes recognized tables from the entire document (all pages) to see if they are multi-page.
        If single-page tables are part of one multi-page, they are combined into one multi-page table.
        """
        multipage_tables = self.multipage_tables_extractor.extract_multipage_tables(single_tables=all_single_tables, lines_with_meta=lines_with_meta)
        return multipage_tables

    def recognize_tables_from_image(self, image: np.ndarray, page_number: int, language: str, table_type: str = "") -> Tuple[np.ndarray, List[ScanTable]]:
        """
        The function recognizes tables with borders from scanned document image.
        Here, the contour analysis method is used to determine the boundaries of table cells.
        Then, a set of heuristics is used to detect tables, and finally,
        the detected table cells are converted to a matrix form (merged cells are detected and separated).
        """
        self.logger.debug(f"Page {page_number}")
        try:
            cleaned_image, scan_tables = self.__rec_tables_from_img(image, page_num=page_number, language=language, table_type=table_type)
            return cleaned_image, scan_tables
        except Exception as ex:
            traceback_message = "".join(traceback.format_exception(type(ex), value=ex, tb=ex.__traceback__))
            logging.warning(traceback_message)

            return image, []

    def detect_tables_prepared(self, image: np.ndarray, page_number: int, language: str, table_type: str = "") -> Tuple[np.ndarray, Optional[dict]]:
        """Staged pipeline, CPU part 1/2 (see pdf_stages ``_table``): detect + filter tables and stack their cells
        WITHOUT running cell OCR, so the recognizer can be OCR'd on the GPU worker. Returns ``(cleaned_image,
        prepared)`` where ``cleaned_image`` has the (kept) table cells masked out for the downstream body OCR and
        ``prepared`` carries the pruned tree + stacked cell images for :meth:`assemble_tables_from_ocr`
        (``None`` when no table survives -> caller emits ``tables=[]``)."""
        from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
        from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_cell_extractor import OCRCellExtractor
        from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.img_processing import detect_table_tree
        try:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            tree, rot_image, _contours, angle = detect_table_tree(gray_image, table_type=table_type, config=self.config)
            pairs = self.onepage_tables_extractor.build_tables_from_tree(gray_image, page_number, tree, angle, table_type)
            if self.table_type.detect_one_cell_table in table_type:
                kept = pairs
            else:
                kept = [(sub, table) for sub, table in pairs if not self.__is_not_table(table, gray_image)]

            cleaned_image = self.__clean_image_from_table(image=image, tables=[table for _, table in kept])
            if not kept:
                return cleaned_image, None

            tree.children = [sub for sub, _ in kept]  # prune to the tables that survived filtering
            nodes = TableTree.collect_cell_nodes(tree)
            batches, stacks = OCRCellExtractor(config=self.config).prepare_batches(rot_image, nodes) if nodes else ([], [])
            prepared = {"tree": tree, "nodes": nodes, "batches": batches, "stacks": stacks, "angle": angle,
                        "page_number": page_number, "table_type": table_type}
            return cleaned_image, prepared
        except Exception as ex:
            logging.warning("".join(traceback.format_exception(type(ex), value=ex, tb=ex.__traceback__)))
            return image, None

    def assemble_tables_from_ocr(self, image: np.ndarray, prepared: dict, ocr_results: list) -> List[ScanTable]:
        """Staged pipeline, CPU part 2/2: assign the GPU cell-OCR results onto the prepared tree, then rebuild the
        (already-filtered) ScanTables with their cell text. ``image`` supplies page dimensions (and pixels for the
        optional split-last-column heuristic)."""
        from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_cell_extractor import OCRCellExtractor
        try:
            tree, nodes, table_type = prepared["tree"], prepared["nodes"], prepared["table_type"]
            if nodes:
                lines_with_meta = OCRCellExtractor(config=self.config).assign_from_ocr(image, nodes, prepared["batches"], prepared["stacks"], ocr_results)
                for node, lines in zip(nodes, lines_with_meta):
                    node.lines = lines
            return [table for _, table in self.onepage_tables_extractor.build_tables_from_tree(image, prepared["page_number"], tree, prepared["angle"], table_type)]
        except Exception as ex:
            logging.warning("".join(traceback.format_exception(type(ex), value=ex, tb=ex.__traceback__)))
            return []

    def __rec_tables_from_img(self, src_image: np.ndarray, page_num: int, language: str, table_type: str) -> Tuple[np.ndarray, List[ScanTable]]:
        gray_image = cv2.cvtColor(src_image, cv2.COLOR_BGR2GRAY) if len(src_image.shape) == 3 else src_image

        single_page_tables = self.onepage_tables_extractor.extract_onepage_tables_from_image(
            image=gray_image,
            page_number=page_num,
            language=language,
            table_type=table_type)

        if self.config.get("labeling_mode", False):
            self.__save_tables(tables=single_page_tables, image=src_image, table_path=self.config.get("table_path", "/tmp/tables"))
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
                image_copy = fill_bbox_on_image(image_copy, location.bbox)
        return image_copy

    def __filter_bad_tables(self, tables: List[ScanTable], image: np.ndarray) -> List[ScanTable]:
        filtered = []
        for table in tables:
            if not self.__is_not_table(table, image):
                filtered.append(table)
        return filtered

    def __is_not_table(self, table: ScanTable, image: np.ndarray) -> bool:
        bbox = table.location.bbox
        height, width = image.shape
        table_image = image[max(bbox.y_top_left, 0): min(bbox.y_bottom_right, height), max(bbox.x_top_left, 0): min(bbox.x_bottom_right, width)]
        mean = table_image.mean()
        std = table_image.std()
        white_mean = (table_image > 225).mean()
        black_mean = (table_image < 225).mean()
        table_area = bbox.square
        cells_area = sum([cell.bbox.square for row in table.cells for cell in row])

        ratio = cells_area / table_area
        res = (white_mean < 0.5) or (black_mean > 0.3) or (std < 30) or (mean < 150) or (mean < 200 and std < 80) or ratio < 0.65
        return res

    def __save_tables(self, tables: List[ScanTable], image: np.ndarray, table_path: Optional[str] = None) -> None:
        image = Image.fromarray(image)
        os.makedirs(table_path, exist_ok=True)
        for table in tables:
            file_name = str(int(time.time()))
            image_path = os.path.join(table_path, f"{file_name}.png")
            jsons_path = os.path.join(table_path, f"{file_name}.json")
            image.save(image_path)
            with open(jsons_path, "w") as out:
                json.dump(obj=table.to_dict(), fp=out, indent=4, ensure_ascii=False)
