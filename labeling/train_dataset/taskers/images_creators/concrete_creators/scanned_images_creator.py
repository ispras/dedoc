import json
import os
import tempfile
import zipfile
from copy import deepcopy
from itertools import zip_longest
from typing import Iterator, List, Optional

import PIL
import cv2
import numpy as np
from PIL.Image import Image
from pdf2image import convert_from_path

from dedoc.utils.image_utils import draw_rectangle
from dedoc.utils.train_dataset_utils import get_original_document_path
from train_dataset.taskers.images_creators.concrete_creators.abstract_images_creator import AbstractImagesCreator


class ScannedImagesCreator(AbstractImagesCreator):

    def __init__(self, path2docs: str) -> None:
        self.path2docs = path2docs

    def add_images(self, page: List[dict], archive: zipfile.ZipFile) -> None:
        """
        take list of line with meta (all lines from one document) and creates images with a bbox around the line
        @param page: list
        @param archive: in this archive we save images
        @return:
        """
        path = get_original_document_path(self.path2docs, page)
        page = [line for line in page if self.__get_bbox_annotations(line)]
        if path.endswith(".pdf"):
            images = self._create_image_pdf(path=path, page=page)
        else:
            images = self._create_image_jpg(path=path, page=page)

        for image, line in zip_longest(images, page):
            if image is None:
                continue

            img_name = f"{line['_uid']}.jpg"
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
        return image_name.lower().endswith(("png", "jpg", "jpeg", "pdf"))

    def _create_image_pdf(self, path: str, page: List[dict]) -> Iterator[Image]:
        current_image = None
        current_page = None
        for line in page:
            page_id = line["_metadata"]["page_id"] + 1
            if current_image is None or current_page != page_id:
                current_page = page_id
                current_image = convert_from_path(path, first_page=current_page, last_page=current_page + 1)[0]
            image = deepcopy(current_image)
            image_bbox = self.__draw_one_bbox(image, line, pdf_image=True)
            if image_bbox is None:
                yield image_bbox
                continue

            image_bbox = PIL.Image.fromarray(image_bbox)
            image_bbox = image_bbox.convert("RGB")
            yield image_bbox

    def _create_image_jpg(self, path: str, page: List[dict]) -> Iterator[Optional[Image]]:
        image = PIL.Image.open(path)
        for line in page:
            image_bbox = self.__draw_one_bbox(image, line)
            if image_bbox is None:
                yield image_bbox
                continue

            image_bbox = PIL.Image.fromarray(image_bbox)
            image_bbox = image_bbox.convert("RGB")
            yield image_bbox

    def __draw_one_bbox(self, image: PIL.Image, line: dict, pdf_image: bool = False) -> Optional[np.ndarray]:
        try:
            bbox_annotation = self.__get_bbox_annotations(line)[0]
            bbox = json.loads(bbox_annotation["value"])
            if pdf_image:
                image = image.resize(size=(bbox["page_width"], bbox["page_height"]), resample=PIL.Image.BICUBIC)
            image_bbox = draw_rectangle(
                image=image,
                x_top_left=int(bbox["x_top_left"] * bbox["page_width"]),
                y_top_left=int(bbox["y_top_left"] * bbox["page_height"]),
                width=bbox["width"] * bbox["page_width"],
                height=bbox["height"] * bbox["page_height"],
                color=line.get("color", (0, 0, 0))
            )
            image_bbox = cv2.resize(np.array(image_bbox), (1276, 1754))
        except Exception as e:
            print(e)  # noqa
            return None
        return image_bbox

    def __get_bbox_annotations(self, line: dict) -> List[dict]:
        bbox_annotations = [annotation for annotation in line["_annotations"] if annotation["name"] == "bounding box"]
        return bbox_annotations
