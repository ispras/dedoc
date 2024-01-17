import json
import os
from typing import List

import PIL
import numpy as np
from PIL.Image import Image


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
    images_path = os.path.join(get_path_original_documents(config), document_name.split(".")[0])
    os.makedirs(images_path, exist_ok=True)
    return images_path


def save_line_with_meta(lines: List["LineWithMeta"], original_document: str, *, config: dict) -> None:  # noqa
    __create_images_path(config)

    # merge lines with the same bbox
    lines = __postprocess_lines(lines)

    with open(os.path.join(config["intermediate_data_path"], "lines.jsonlines"), "a") as out:
        for line in lines:
            # setattr(line, "uid", line.metadata.bbox_uid)
            line_dict = json.loads(json.dumps(line, default=lambda o: o.__dict__, ensure_ascii=False))
            line_dict["original_document"] = os.path.basename(original_document)
            out.write(json.dumps(line_dict, ensure_ascii=False))
            out.write("\n")


def __postprocess_lines(lines: List["LineWithMeta"]) -> List["LineWithMeta"]:  # noqa
    postprocessed_lines = []
    prev_bbox = None
    for line in lines:
        bbox_annotations = [annotation for annotation in line.annotations if annotation.name == "bounding box"]
        if not bbox_annotations:
            postprocessed_lines.append(line)
            continue

        bbox = bbox_annotations[0].value
        if not prev_bbox or prev_bbox != bbox:
            postprocessed_lines.append(line)
            prev_bbox = bbox
            continue
        postprocessed_lines[-1] += line

    return postprocessed_lines


def get_original_document_path(path2documents: str, page: List[dict]) -> str:
    return os.path.join(path2documents, page[0]["original_document"])
