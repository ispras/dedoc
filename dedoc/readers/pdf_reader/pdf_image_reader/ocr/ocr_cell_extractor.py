import logging
import os
from typing import Iterator, List, Optional, Tuple

import cv2
import numpy as np
from dedocutils.data_structures import BBox

from dedoc.data_structures import BBoxAnnotation, ConfidenceAnnotation, LineMetadata, LineWithMeta
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_line_extractor import OCRLineExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_page import OcrPage
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_cells
from dedoc.utils.image_utils import get_highest_pixel_frequency
from dedoc.utils.parameter_utils import get_path_param


class OCRCellExtractor:
    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.config = config
        self.line_extractor = OCRLineExtractor(config=config)
        self.logger = config.get("logger", logging.getLogger())

    def get_cells_text(self, page_image: np.ndarray, tree_nodes: List["TableTree"], language: str) -> List[List[LineWithMeta]]:  # noqa
        for node in tree_nodes:
            node.set_crop_text_box(page_image)

        tree_nodes.sort(key=lambda t: -t.crop_text_box.width)
        originalbox_to_fastocrbox = {}
        batches = list(self.__nodes2batch(tree_nodes))
        for num_batch, nodes_batch in enumerate(batches):

            if self.config.get("debug_mode", False):
                tmp_dir = os.path.join(get_path_param(self.config, "path_debug"), "debug_tables/batches/")
                os.makedirs(tmp_dir, exist_ok=True)
                for i, table_tree_node in enumerate(nodes_batch):
                    cv2.imwrite(os.path.join(tmp_dir, f"image_{num_batch}_{i}.png"), BBox.crop_image_by_box(page_image, table_tree_node.cell_box))

            ocr_result, chunk_boxes = self.__handle_one_batch(src_image=page_image, tree_table_nodes=nodes_batch, num_batch=num_batch, language=language)

            for chunk_index, _ in enumerate(chunk_boxes):
                originalbox_to_fastocrbox[nodes_batch[chunk_index].cell_box] = []

            # we find mapping
            for line in list(ocr_result.lines):
                chunk_index = 0
                line_center_y = line.bbox.y_top_left + int(line.bbox.height / 2)
                while chunk_index < len(chunk_boxes) and line_center_y > chunk_boxes[chunk_index].y_top_left:
                    chunk_index += 1
                chunk_index -= 1

                # save bbox mapping:
                for word in line.words:
                    # do relative coordinates (inside cell_image)
                    word.bbox.y_top_left -= chunk_boxes[chunk_index].y_top_left
                    word.bbox.x_top_left -= chunk_boxes[chunk_index].x_top_left
                    # do absolute coordinate on src_image (inside src_image)
                    word.bbox.y_top_left += nodes_batch[chunk_index].crop_text_box.y_top_left
                    word.bbox.x_top_left += nodes_batch[chunk_index].crop_text_box.x_top_left

                originalbox_to_fastocrbox[nodes_batch[chunk_index].cell_box].append(line.words)

        return self.__create_lines_with_meta(tree_nodes, originalbox_to_fastocrbox, page_image)

    def __handle_one_batch(self, src_image: np.ndarray, tree_table_nodes: List["TableTree"], num_batch: int, language: str = "rus") -> Tuple[OcrPage, List[BBox]]: # noqa
        concatenated, chunk_boxes = self.__concat_images(src_image=src_image, tree_table_nodes=tree_table_nodes)
        if self.config.get("debug_mode", False):
            debug_dir = os.path.join(get_path_param(self.config, "path_debug"), "debug_tables", "batches")
            os.makedirs(debug_dir, exist_ok=True)
            image_path = os.path.join(debug_dir, f"stacked_batch_image_{num_batch}.png")
            cv2.imwrite(image_path, concatenated)
        ocr_result = get_text_with_bbox_from_cells(concatenated, language, ocr_conf_threshold=0.0)

        return ocr_result, chunk_boxes

    def __concat_images(self, src_image: np.ndarray, tree_table_nodes: List["TableTree"]) -> Tuple[np.ndarray, List[BBox]]:  # noqa
        space = 10
        width = max((tree_node.crop_text_box.width + space for tree_node in tree_table_nodes))
        height = sum((tree_node.crop_text_box.height + space for tree_node in tree_table_nodes))
        # new_im = Image.fromarray(np.zeros((height, width), dtype=np.uint8) + 255)
        stacked_image = np.full((height, width), fill_value=255, dtype=np.uint8)

        y_prev = 0
        chunk_boxes = []
        for tree_node in tree_table_nodes:
            x_coord = space
            cell_image = BBox.crop_image_by_box(src_image, tree_node.crop_text_box)
            if self.config.get("debug_mode", False):
                debug_dir = os.path.join(get_path_param(self.config, "path_debug"), "debug_tables", "batches")
                os.makedirs(debug_dir, exist_ok=True)
                image_path = os.path.join(debug_dir, "cell_croped.png")
                cv2.imwrite(image_path, cell_image)
            cell_height, cell_width = cell_image.shape[0], cell_image.shape[1]

            stacked_image[y_prev:y_prev + cell_height, x_coord:x_coord + cell_width] = cell_image
            # new_im.paste(image, (x_coord, y_coord))
            # y_coord += cell_image.shape[1] + space
            inserted_image_height = cell_height + space
            chunk_boxes.append(BBox(x_top_left=x_coord, y_top_left=y_prev, width=width - x_coord, height=inserted_image_height))
            # borders.append((y_prev, y_coord))
            y_prev += inserted_image_height

        assert len(chunk_boxes) == len(tree_table_nodes)
        return stacked_image, chunk_boxes

    def __nodes2batch(self, tree_nodes: List["TableTree"]) -> Iterator[List["TableTree"]]:  # noqa
        batch = []
        width = 0
        height = 0
        for node in tree_nodes:
            image_height, image_width = node.crop_text_box.height, node.crop_text_box.width
            width = max(width, image_width)
            height += image_height
            if (width * height > 10 ** 7 or width > 1.5 * image_width) and len(batch) > 0:
                yield batch
                batch = []
                width = 0
                height = 0
            batch.append(node)
        if len(batch) > 0:
            yield batch

    def __create_lines_with_meta(self, tree_nodes: List["TableTree"], original_box_to_fast_ocr_box: dict, original_image: np.ndarray) -> List[List[LineWithMeta]]:  # noqa
        nodes_lines = []

        for node in tree_nodes:
            # create new line
            cell_lines = []

            for line in original_box_to_fast_ocr_box[node.cell_box]:  # step inside results of fast-ocr
                text_line = OCRCellExtractor.get_line_with_meta("")
                for word in line:
                    # add space between words
                    if len(text_line) != 0:
                        text_line += OCRCellExtractor.get_line_with_meta(" ", bbox=word.bbox, image=original_image)
                    # add confidence value
                    text_line += OCRCellExtractor.get_line_with_meta(text=word.text, bbox=word.bbox, image=original_image,
                                                                     confidences=[
                                                                         ConfidenceAnnotation(start=0, end=len(word.text), value=word.confidence / 100.)
                                                                     ])
                if len(text_line) > 0:  # add new line
                    cell_lines.append(text_line)

            nodes_lines.append(cell_lines)

        return nodes_lines

    @staticmethod
    def get_line_with_meta(text: str,
                           bbox: Optional[BBox] = None,
                           image: Optional[np.ndarray] = None,
                           confidences: Optional[List[ConfidenceAnnotation]] = None) -> LineWithMeta:
        annotations = []

        if bbox:
            assert image is not None, "BBox and image arguments should be both specified"
            height, width = image.shape[:2]
            annotations.append(BBoxAnnotation(0, len(text), bbox, page_height=height, page_width=width))

        confidences = [] if confidences is None else confidences
        for confidence in confidences:
            annotations.append(ConfidenceAnnotation(confidence.start, confidence.end, str(confidence.value)))

        return LineWithMeta(line=text, metadata=LineMetadata(page_id=0, line_id=None), annotations=annotations)

    @staticmethod
    def upscale(image: Optional[np.ndarray], padding_px: int = 40) -> Tuple[Optional[np.ndarray], int]:
        if image is None or sum(image.shape) < 5:
            return image, 0

        color_backgr = get_highest_pixel_frequency(image)

        if len(image.shape) == 2:
            bigger_cell = np.full((image.shape[0] + padding_px, image.shape[1] + padding_px), color_backgr)
            bigger_cell[padding_px // 2:-padding_px // 2, padding_px // 2:-padding_px // 2] = image
        else:
            bigger_cell = np.full((image.shape[0] + padding_px, image.shape[1] + padding_px, 3), color_backgr)
            bigger_cell[padding_px // 2:-padding_px // 2, padding_px // 2:-padding_px // 2, :] = image

        return bigger_cell, padding_px // 2
