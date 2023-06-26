import os
import tempfile
import zipfile
from copy import deepcopy
from itertools import zip_longest
from typing import List, Iterator

import PIL
import cv2
import numpy as np
from PIL.Image import Image
from pdf2image import convert_from_path

from dedoc.train_dataset.data_structures.images_archive import ImagesArchive
from dedoc.train_dataset.taskers.images_creators.concrete_creators.abstract_images_creator import AbstractImagesCreator
from dedoc.train_dataset.train_dataset_utils import get_original_document_path
from dedoc.utils.image_utils import draw_rectangle


class ScannedImagesCreator(AbstractImagesCreator):

    def __init__(self, path2docs: str) -> None:
        self.path2docs = path2docs

    @staticmethod
    def _draw_one_bbox(image: np.ndarray, line: dict) -> np.ndarray:
        bbox = line["bbox"]["bbox"]
        image_bbox = draw_rectangle(image=image,
                                    x_top_left=bbox["x_top_left"],
                                    y_top_left=bbox["y_top_left"],
                                    width=bbox["width"],
                                    height=bbox["height"],
                                    color=line.get("color", "black"))
        image_bbox = cv2.resize(np.array(image_bbox), (1276, 1754))
        return image_bbox

    def add_images(self, page: List[dict], archive: zipfile.ZipFile) -> None:
        """
        take list of line with meta (all lines from one document) and creates images with a bbox around the line
        @param page: list
        @param archive: in this archive we save images
        @return:
        """
        path = get_original_document_path(self.path2docs, page)
        page = [line for line in page if "bbox" in line]
        if path.endswith("pdf"):
            images = self._create_image_pdf(path=path, page=page)
        elif path.endswith("zip"):
            images = self._create_image_zip(path=path, page=page)
        else:
            images = self._create_image_jpg(path=path, page=page)
        for image, line in zip_longest(images, page):
            img_name = "{}.jpg".format(line["_uid"])
            with tempfile.TemporaryDirectory() as tmpfile:
                img_path = os.path.join(tmpfile, img_name)
                image.save(img_path, format="jpeg")
                archive.write(img_path, img_name)

    def can_read(self, page: List[dict]) -> bool:
        """
        return if this creator can handle this document type
        @param page:
        @return:
        """
        image_name = get_original_document_path(self.path2docs, page)
        return image_name.endswith(("png", "jpg", "jpeg", "pdf", "zip"))

    def _create_image_zip(self, path: str, page: List[dict]) -> Iterator[Image]:
        current_image = None
        current_page = None
        archive = ImagesArchive(path)
        for line in page:
            page_id = line["_metadata"]["page_id"]
            if current_image is None or current_page != page_id:
                current_page = page_id
                current_image = archive.get_page(page_id)
            image = deepcopy(current_image)
            image_bbox = self._draw_one_bbox(image, line)
            image_bbox = PIL.Image.fromarray(image_bbox)
            image_bbox = image_bbox.convert('RGB')
            yield image_bbox

    def _create_image_pdf(self, path: str, page: List[dict]) -> Iterator[Image]:
        current_image = None
        current_page = None
        for line in page:
            page_id = line["_metadata"]["page_id"] + 1
            if current_image is None or current_page != page_id:
                current_page = page_id
                current_image = convert_from_path(path, first_page=current_page, last_page=current_page + 1)[0]
            image = deepcopy(current_image)
            image_bbox = self._draw_one_bbox(image, line)
            image_bbox = PIL.Image.fromarray(image_bbox)
            image_bbox = image_bbox.convert('RGB')
            yield image_bbox

    def _create_image_jpg(self, path: str, page: List[dict]) -> Iterator[Image]:
        image = PIL.Image.open(path)
        for line in page:
            image_bbox = self._draw_one_bbox(image, line)
            image_bbox = PIL.Image.fromarray(image_bbox)
            image_bbox = image_bbox.convert('RGB')
            yield image_bbox
