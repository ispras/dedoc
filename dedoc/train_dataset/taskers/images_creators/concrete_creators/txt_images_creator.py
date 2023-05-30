import logging
import os
import tempfile
import zipfile
from typing import List, Tuple

from PIL import ImageFont, ImageDraw, Image
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader

from dedoc.train_dataset.taskers.images_creators.concrete_creators.abstract_images_creator import AbstractImagesCreator
from dedoc.train_dataset.train_dataset_utils import get_original_document_path
from dedoc.utils.utils import get_batch


class TxtImagesCreator(AbstractImagesCreator):
    # TODO отдебажить
    def __init__(self, path2docs: str, *, config: dict) -> None:
        self.path2docs = path2docs

        self.max_characters = 80
        self.max_lines = 40
        self.horizontal_padding = 20
        self.vertical_padding = 40

        self.row_height = 36
        self.font_size = self.row_height - 8
        self.row_width = int(self.max_characters * self.row_height / 2.5)

        self.text_color = (0, 0, 0)
        self.background_color = (255, 255, 255)
        self.border_color = (0, 0, 0)

        font_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "resources", "Arial_Narrow.ttf"))
        self.font = ImageFont.truetype(font_path, self.font_size)

        self.txt_reader = RawTextReader(config=config)
        self.logger = config.get("logger", logging.getLogger())

    def add_images(self, page: List[dict], archive: zipfile.ZipFile) -> None:
        """
        take list of line with meta (all lines from one document) and creates images with a bbox around the line
        @param page: list
        @param archive: archive where this image creator should put image, named <uid>.jpg
        @return:
        """
        path2doc = get_original_document_path(self.path2docs, page)
        doc = self.txt_reader.read(path2doc, parameters={})

        txt_lines = self.__make_text_lines(doc.lines)

        for batch_index, batch_lines in enumerate(get_batch(self.max_lines, txt_lines)):
            batch_start = batch_index * self.max_lines
            txt_lines_count = sum([len(line) for line in batch_lines])
            width = self.horizontal_padding * 2 + self.row_width
            height = self.vertical_padding * 2 + max(self.max_lines, txt_lines_count) * self.row_height

            for i, (uid, line) in enumerate(batch_lines):
                if line[0].isspace():
                    self.logger.info(
                        "\n{} / {} image processed (empty line)".format(i + batch_start + 1, len(txt_lines)))
                    continue

                image = self.__make_image(width, height, batch_lines)
                self.logger.info("\n{} / {} image processed".format(i + batch_start + 1, len(txt_lines)))
                image_with_bbox = self.__make_bbox_image(image, batch_lines, i)
                img_name = "{}.jpg".format(uid)
                with tempfile.TemporaryDirectory() as tmpdir:
                    img_path = os.path.join(tmpdir, img_name)
                    image_with_bbox.save(img_path, format="jpeg")
                    archive.write(img_path, img_name)

    def can_read(self, page: List[dict]) -> bool:
        """
        return if this creator can handle this document type
        @param page:
        @return:
        """
        image_name = get_original_document_path(self.path2docs, page)
        return image_name.endswith("txt")

    def __split_long_line(self, line: str) -> List[str]:
        words = line.split()

        # if no words in this very long line
        if len(words) == 1:
            parts = (len(line) + self.max_characters) // self.max_characters
            return [line[i:i + self.max_characters] for i in range(parts)]

        splited_lines = []
        curr_line = []
        curr_len = 0

        for word in words:
            if curr_len + len(curr_line) - 1 + len(word) >= self.max_characters:
                splited_lines.append(" ".join(curr_line))
                curr_line = []
                curr_len = 0

            curr_len += len(word)
            curr_line.append(word)

        splited_lines.append(" ".join(curr_line))
        return splited_lines

    def __make_text_lines(self, page: List[LineWithMeta]) -> List[Tuple[str, List[str]]]:
        txt_lines = []

        for line in page:
            if len(line.line) <= self.max_characters:
                split_line = [line.line]
            else:
                split_line = self.__split_long_line(line.line)
            txt_lines.append((line.uid, split_line))
        return txt_lines

    def __make_image(self, width: int, height: int, txt_lines: List[Tuple[str, List[str]]]) -> Image:
        image = Image.new('RGB', (width, height), color=self.background_color)

        draw = ImageDraw.Draw(image)
        x = self.horizontal_padding
        y = self.vertical_padding

        for i, (uid, line) in enumerate(txt_lines):
            for part in line:
                draw.text((x, y), part, font=self.font, fill=self.text_color)
                y += self.row_height

        return image

    def __make_bbox_image(self, image: Image, txt_lines: List[Tuple[str, List[str]]], draw_index: int) -> Image:
        draw = ImageDraw.Draw(image)
        x = self.horizontal_padding
        y = self.vertical_padding + sum([len(line) for _, line in txt_lines[:draw_index]]) * self.row_height

        w, h = self.row_width, len(txt_lines[draw_index]) * self.row_height
        draw.rectangle([(x - 1, y - 1), (x + w + 2, y + h + 2)], outline=self.border_color)

        return image
