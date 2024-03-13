import dataclasses
import logging
import os
import tempfile
import zipfile
from typing import List, Optional, Tuple

import PIL
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dedocutils.data_structures import BBox

from dedoc.utils.image_utils import draw_rectangle
from dedoc.utils.train_dataset_utils import get_original_document_path
from train_dataset.taskers.images_creators.concrete_creators.abstract_images_creator import AbstractImagesCreator


@dataclasses.dataclass
class LineLocation:
    image_name: str
    bbox: BBox


class TxtImagesCreator(AbstractImagesCreator):
    def __init__(self, path2docs: str, *, config: dict) -> None:
        self.path2docs = path2docs

        # text drawing settings
        self.font_size = 25
        self.page_size = (1240, 1750)
        self.page_color = (255, 255, 255)
        self.text_color = (0, 0, 0)
        self.word_space = 0.5
        self.line_gap = 10
        self.margin = 35

        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "Arial_Narrow.ttf"))
        self.font = ImageFont.truetype(font_path, self.font_size)

        self.logger = config.get("logger", logging.getLogger())
        self.logging_step = 50

    def can_read(self, page: List[dict]) -> bool:
        file_name = get_original_document_path(self.path2docs, page)
        return file_name.lower().endswith(".txt")

    def add_images(self, page: List[dict], archive: zipfile.ZipFile) -> None:
        """
        1 - draw text for all document lines (create several pages)
        2 - for each line get a page with one line highlighted by bounding box
        """
        len_page = len(page)

        with tempfile.TemporaryDirectory() as tmpdir:
            self.logger.info("Draw images with text")
            location_list = self.__draw_pages(page, tmpdir)

            self.logger.info("Draw bounding boxes on images")
            for line_num, line_dict in enumerate(page, start=1):
                if line_num % self.logging_step == 0:
                    self.logger.info(f"{line_num}/{len_page} bboxes")

                line_location = location_list[line_num - 1]
                if line_location is None:
                    continue

                image = PIL.Image.open(os.path.join(tmpdir, line_location.image_name))
                image_with_bbox = draw_rectangle(
                    image=image,
                    x_top_left=line_location.bbox.x_top_left,
                    y_top_left=line_location.bbox.y_top_left,
                    width=line_location.bbox.width,
                    height=line_location.bbox.height,
                    color=line_dict.get("color", (0, 0, 0))
                )
                image_with_bbox = PIL.Image.fromarray(image_with_bbox).convert("RGB")

                img_name = f'{line_dict["_uid"]}.jpg'
                with tempfile.TemporaryDirectory() as tmpfile:
                    img_path = os.path.join(tmpfile, img_name)
                    image_with_bbox.save(os.path.join(tmpfile, img_name), format="jpeg")
                    archive.write(img_path, img_name)

    def __draw_pages(self, page: List[dict], tmpdir: str) -> List[Optional[LineLocation]]:
        location_list = [None for _ in page]
        len_page = len(page)
        page_number = 0

        x, y = self.margin, self.margin
        img, draw = self.__create_page()

        for line_num, line_dict in enumerate(page, start=1):
            if line_num % self.logging_step == 0:
                self.logger.info(f"{line_num}/{len_page} lines")

            words = line_dict["_line"].strip().split()
            if len(words) == 0:
                continue

            line_bbox, line_ended = None, False
            y_top_left = y

            for word in words:
                x_min, y_min, x_max, y_max = draw.textbbox((x, y), word, self.font)
                if x_max + self.margin >= self.page_size[0]:
                    x = self.margin
                    y += self.font_size + self.line_gap

                if y_max + self.margin >= self.page_size[1]:
                    img.save(os.path.join(tmpdir, f"{page_number}.jpg"), format="jpeg")
                    page_number += 1
                    img, draw = self.__create_page()
                    x, y = self.margin, self.margin
                    y_top_left = y

                    if line_bbox is not None:
                        location_list[line_num - 1] = LineLocation(image_name=f"{page_number - 1}.jpg", bbox=line_bbox)
                        line_ended = True
                        break

                x_min, y_min, x_max, y_max = draw.textbbox((x, y), word, self.font)
                draw.text((x, y), word, self.text_color, font=self.font)
                line_bbox = BBox.from_two_points(top_left=(self.margin, y_top_left), bottom_right=(self.page_size[0] - self.margin, y + self.font_size))
                x = x_max + int(self.word_space * self.font_size)

            if line_ended:
                continue

            location_list[line_num - 1] = LineLocation(image_name=f"{page_number}.jpg", bbox=line_bbox)
            y += self.font_size + self.line_gap
            x = self.margin

        img.save(os.path.join(tmpdir, f"{page_number}.jpg"), format="jpeg")
        return location_list

    def __create_page(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        img_arr = np.zeros((self.page_size[1], self.page_size[0], 3), dtype=np.uint8)
        img_arr[:, :] = self.page_color
        img = Image.fromarray(img_arr)
        draw = ImageDraw.Draw(img)
        return img, draw
