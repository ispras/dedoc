import logging
import os
from typing import List, Tuple, Iterator, Optional
import numpy as np
from PIL import Image

from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_line_extractor import OCRLineExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_cell_text_by_ocr
from dedoc.utils.image_utils import crop_image_text, get_highest_pixel_frequency


class OCRCellExtractor:
    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.config = config
        self.line_extractor = OCRLineExtractor(config=config)
        self.logger = config.get("logger", logging.getLogger())

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
                    tmp_dir = os.path.join(tmp_dir, "{}".format(len(os.listdir(tmp_dir))))
                    os.makedirs(tmp_dir, exist_ok=True)
                    for i, image in enumerate(batch):
                        image.save(os.path.join(tmp_dir, "image_{}.png".format(i)))

                res.extend(self.__handle_one_batch(batch, language))
            assert len(res) == len(img_cells)
            return [text for _, text in sorted(zip(ids, res))]
        except Exception as e:
            if self.config.get("debug_mode", False):
                raise e
            else:
                self.logger.warning(str(e))
            return [get_cell_text_by_ocr(np.array(image), language) for image in map(self.upscale, img_cells)]

    def get_cells_rotated(self, img_cells: List[np.ndarray], language: str) -> List[str]:
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
