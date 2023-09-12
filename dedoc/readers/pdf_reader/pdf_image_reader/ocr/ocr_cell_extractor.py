import logging
import os
from typing import Iterator, List, Optional, Tuple

import cv2
import numpy as np

from dedoc.data_structures import BBoxAnnotation, ConfidenceAnnotation, LineMetadata, LineWithMeta
from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_line_extractor import OCRLineExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_page import OcrPage
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_cells
from dedoc.utils.image_utils import crop_image_text


class OCRCellExtractor:
    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.config = config
        self.line_extractor = OCRLineExtractor(config=config)
        self.logger = config.get("logger", logging.getLogger())

    def get_cells_text_2(self, page_image: np.ndarray, tree_nodes: List[TableTree], language: str) -> List[List[LineWithMeta]]:
        # try:
        # if len(img_cells) == 0:
        #    return []
        for node in tree_nodes:
            cell_image = BBox.crop_image_by_box(page_image, node.cell_box)
            node.crop_text_box = crop_image_text(cell_image)
        # img_cells_cropped = map(crop_image_text, img_cells)
        # ids, images = zip(*sorted(enumerate(img_cells_cropped), key=lambda t: -t[1].shape[1]))
        tree_nodes.sort(key=lambda t: -t.crop_text_box.width)  # TODO check
        originalbox_to_fastocrbox = {}
        for num_batch, batch in enumerate(self.__images2batch_2(tree_nodes)):

            if self.config.get("debug_mode", False):
                tmp_dir = "/tmp/docreader/debug_tables/batches/"
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_dir = os.path.join(tmp_dir, f"{len(os.listdir(tmp_dir))}")
                os.makedirs(tmp_dir, exist_ok=True)
                for i, image in enumerate(batch):
                    image.save(os.path.join(tmp_dir, f"image_{i}.png"))

            ocr_result, chunk_boxes = self.__handle_one_batch_2(src_image=page_image, tree_table_nodes=batch, num_batch=num_batch,
                                                                language=language)

            for chunk_index in enumerate(chunk_boxes):
                originalbox_to_fastocrbox[batch[chunk_index].cell_bbox] = []

            # we find mapping
            for line in list(ocr_result.lines):
                chunk_index = 0
                line_center_y = line.bbox.y_top_left + int(line.bbox.height / 2)
                while chunk_index < len(chunk_boxes) and line_center_y > batch[chunk_index][2]:
                    chunk_index += 1
                chunk_index -= 1

                # save bbox mapping:
                for word in line.words:
                    # do relative coordinates (inside cell_image)
                    word.bbox.y_top_left -= chunk_boxes[chunk_index].y_top_left
                    word.bbox.x_top_left -= chunk_boxes[chunk_index].x_top_left
                    # do absolute coordinate on src_image (inside src_image)
                    word.bbox.y_top_left += batch[chunk_index].cell_bbox.y_top_left
                    word.bbox.x_top_left += batch[chunk_index].cell_bbox.x_top_left

                originalbox_to_fastocrbox[batch[chunk_index].cell_bbox].append(line.words)

        return self.__create_lines_with_meta(tree_nodes, originalbox_to_fastocrbox, page_image)

    """   except Exception as e:
            if self.config.get("debug_mode", False):
                raise e
            else:
                self.logger.warning(str(e))
            return [get_cell_text_by_ocr(np.array(image), language) for image in map(self.upscale, img_cells)]"""

    def __handle_one_batch_2(self, src_image: np.ndarray, tree_table_nodes: List[TableTree], num_batch: int, language: str = "rus") -> (
            Tuple)[OcrPage, List[BBox]]:
        concatenated, chunk_boxes = self.__concat_images_2(src_image=src_image, tree_table_nodes=tree_table_nodes)
        cv2.imwrite(self.config.get("path_debug") + f"stacked_batch_image_{num_batch}.png", concatenated)
        ocr_result = get_text_with_bbox_from_cells(concatenated, language, ocr_conf_threshold=0.0)

        return ocr_result, chunk_boxes

    def __concat_images_2(self, src_image: np.ndarray, tree_table_nodes: List[TableTree]) -> Tuple[np.ndarray, List[BBox]]:
        space = 10
        width = max((tree_node.crop_text_box.width + space for tree_node in tree_table_nodes))
        height = sum((tree_node.crop_text_box.height + space for tree_node in tree_table_nodes))
        # new_im = Image.fromarray(np.zeros((height, width), dtype=np.uint8) + 255)
        stacked_image = np.full((height, width), fill_value=255, dtype=np.uint8)

        y_coord = 0
        y_prev = 0
        chunk_boxes = []
        for tree_node in tree_table_nodes:
            x_coord = space
            cell_image = BBox.crop_image_by_box(src_image, tree_node.crop_text_box)
            stacked_image[y_coord:y_coord + cell_image.shape[0], x_coord + cell_image.shape[1]] = cell_image
            # new_im.paste(image, (x_coord, y_coord))
            # y_coord += cell_image.shape[1] + space
            inserted_image_height = cell_image.shape[1] + space
            chunk_boxes.append(BBox(x_top_left=x_coord, y_top_left=y_prev, width=width - x_coord, height=inserted_image_height))
            # borders.append((y_prev, y_coord))
            y_prev += inserted_image_height

        assert len(chunk_boxes) == len(tree_table_nodes)
        return stacked_image, chunk_boxes

    def __images2batch_2(self, tree_nodes: List[TableTree]) -> Iterator[List[TableTree]]:
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
            batch.append(tree_nodes)
        if len(batch) > 0:
            yield batch

    def __create_lines_with_meta(self, tree_nodes: List[TableTree], original_box_to_fast_ocr_box: dict, original_image: np.ndarray) -> List[List[LineWithMeta]]:
        nodes_lines = []

        for node in tree_nodes:
            # create new line
            cell_lines = []

            for line in original_box_to_fast_ocr_box[node.cell_box]:  # step inside results of fast-ocr
                text_line = self.get_line_with_meta("")
                for word in line:
                    # add space between words
                    if len(text_line) != 0:
                        text_line += self.get_line_with_meta(" ", bbox=word.bbox, image=original_image)
                    # add confidence value
                    text_line += self.get_line_with_meta(text=word.text, bbox=word.bbox, image=original_image,
                                                         confidences=[ConfidenceAnnotation(start=0, end=len(word.text), value=word.confidence / 100.)])
                if len(text_line) > 0:  # add new line
                    cell_lines.append(text_line)

            nodes_lines.append(cell_lines)

        return nodes_lines

    def get_line_with_meta(self, text: str,
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
            annotations.append(ConfidenceAnnotation(confidence.start, confidence.end, str(confidence.confidence)))

        return LineWithMeta(line=text, metadata=LineMetadata(page_id=0, line_id=None), annotations=annotations)
    """
    def get_cells_text(self, img_cells: List[np.ndarray], language: str) -> List[str]:
        try:
            if len(img_cells) == 0:
                return []
            img_cells_cropped = map(crop_image_text, img_cells)
            ids, images = zip(*sorted(enumerate(img_cells_cropped), key=lambda t: -t[1].shape[1]))
            res = []
            for batch in self.__images2batch(images):
                if self.config.get("debug_mode", False):
                    tmp_dir = "/tmp/docreader/debug_tables/batches/"
                    os.makedirs(tmp_dir, exist_ok=True)
                    tmp_dir = os.path.join(tmp_dir, f"{len(os.listdir(tmp_dir))}")
                    os.makedirs(tmp_dir, exist_ok=True)
                    for i, image in enumerate(batch):
                        image.save(os.path.join(tmp_dir, f"image_{i}.png"))

                res.extend(self.__handle_one_batch(batch, language))
            assert len(res) == len(img_cells)
            return [text for _, text in sorted(zip(ids, res))]
        except Exception as e:
            if self.config.get("debug_mode", False):
                raise e
            else:
                self.logger.warning(str(e))
            return [get_cell_text_by_ocr(np.array(image), language) for image in map(self.upscale, img_cells)]

    @staticmethod
    def upscale(image: Optional[np.ndarray], padding_px: int = 40) -> Optional[np.ndarray]:
        if image is None or sum(image.shape) < 5:
            return image

        color_backgr = get_highest_pixel_frequency(image)

        if len(image.shape) == 2:
            bigger_cell = np.full((image.shape[0] + padding_px, image.shape[1] + padding_px), color_backgr)
            bigger_cell[padding_px // 2:-padding_px // 2, padding_px // 2:-padding_px // 2] = image
        else:
            bigger_cell = np.full((image.shape[0] + padding_px, image.shape[1] + padding_px, 3), color_backgr)
            bigger_cell[padding_px // 2:-padding_px // 2, padding_px // 2:-padding_px // 2, :] = image
        return bigger_cell

    def __bbox_intersection(self, cell_low: int, cell_high: int, bbox: BBox) -> float:
        assert cell_low <= cell_high
        low = max(cell_low, bbox.y_top_left)
        high = min(cell_high, bbox.y_bottom_right)
        if low >= high:
            return 0
        return (high - low) / bbox.height

    def __best_cell(self, borders: List[Tuple[int, int]], bbox: TextWithBBox) -> int:
        res = []
        for i, (low, high) in enumerate(borders):
            res.append((self.__bbox_intersection(low, high, bbox.bbox), i))
        return max(res)[1]

    def __handle_one_batch(self, cells: List[Image.Image], language: str) -> List[str]:
        concatenated, borders = self.__concat_images(images=cells)

        bboxes = self.line_extractor.split_image2lines(image=concatenated, page_num=0, language=language, cells=True)
        cells_text = [[] for _ in cells]
        for bbox in sorted(bboxes.bboxes, key=lambda b: b.bbox.y_top_left):
            cell_id = self.__best_cell(borders, bbox)
            cells_text[cell_id].append(bbox.text)
        return ["".join(cell).strip() for cell in cells_text]

    def __concat_images(self, images: List[Image.Image]) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
        space = 10
        width = max((image.size[0] + space for image in images))
        height = sum((image.size[1] + space for image in images))
        new_im = Image.fromarray(np.zeros((height, width), dtype=np.uint8) + 255)

        y_coord = 0
        y_prev = 0
        borders = []
        for image in images:
            x_coord = space
            new_im.paste(image, (x_coord, y_coord))
            y_coord += image.size[1] + space
            borders.append((y_prev, y_coord))
            y_prev = y_coord
        assert len(borders) == len(images)
        return np.array(new_im), borders

    def __images2batch(self, images: List[np.ndarray]) -> Iterator[List[Image.Image]]:
        batch = []
        width = 0
        height = 0
        for image in images:
            image_height, image_width = image.shape
            width = max(width, image_width)
            height += image_height
            if (width * height > 10 ** 7 or width > 1.5 * image_width) and len(batch) > 0:
                yield batch
                batch = []
                width = 0
                height = 0
            batch.append(Image.fromarray(image))
        if len(batch) > 0:
            yield batch
            """
