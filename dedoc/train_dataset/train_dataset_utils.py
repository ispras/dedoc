import json
import os
import shutil
import zipfile
from typing import List
import numpy as np
import PIL
from PIL.Image import Image

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox


def __to_pil(image: np.ndarray) -> Image:
    return PIL.Image.fromarray(image)


def __create_images_path(config: dict) -> None:
    assert config.get("labeling_mode")
    assert config.get("intermediate_data_path") is not None
    if not os.path.isdir(config.get("intermediate_data_path")):
        os.makedirs(config.get("intermediate_data_path"))


def get_path_original_documents(config: dict) -> str:
    path = os.path.join(config["intermediate_data_path"], "original_documents")
    os.makedirs(path, exist_ok=True)
    return path


def _get_images_path(config: dict, document_name: str) -> str:
    return os.path.join(get_path_original_documents(config), document_name.split(".")[0])


def save_page_with_bbox(page: PageWithBBox, document_name: str, *, config: dict) -> None:
    __create_images_path(config)
    uid = document_name
    images_path = _get_images_path(config=config, document_name=document_name)
    if not os.path.isdir(images_path):
        os.makedirs(images_path)

    with open(os.path.join(config["intermediate_data_path"], "bboxes.jsonlines"), "a") as out:
        image = __to_pil(page.image)
        image_name = "img_{}_{:06d}.png".format(uid, page.page_num)
        image.save(os.path.join(images_path, image_name))
        for bbox in page.bboxes:
            bbox_dict = bbox.to_dict()
            bbox_dict["original_image"] = image_name
            out.write(json.dumps(bbox_dict, ensure_ascii=False))
            out.write("\n")


def _convert2zip(config: dict, document_name: str) -> str:
    images_path = _get_images_path(config=config, document_name=document_name)
    images = [os.path.join(images_path, file) for file in sorted(os.listdir(images_path))]

    archive_filename = images_path + ".zip"
    with zipfile.ZipFile(archive_filename, "w") as archive:
        for image in images:
            archive.write(filename=image, arcname=os.path.basename(image))
    shutil.rmtree(images_path)
    return archive_filename


def save_line_with_meta(lines: List[LineWithMeta], original_document: str, *, config: dict) -> None:

    __create_images_path(config)
    if original_document.endswith((".jpg", ".png", ".pdf")):
        original_document = _convert2zip(config=config, document_name=original_document)

    with open(os.path.join(config["intermediate_data_path"], "lines.jsonlines"), "a") as out:
        for line in lines:
            # setattr(line, "uid", line.metadata.bbox_uid)
            line_dict = json.loads(json.dumps(line, default=lambda o: o.__dict__, ensure_ascii=False))
            line_dict["original_document"] = os.path.basename(original_document)
            out.write(json.dumps(line_dict, ensure_ascii=False))
            out.write("\n")


def get_original_document_path(path2documents: str, page: List[dict]) -> str:
    return os.path.join(path2documents, page[0]["original_document"])
