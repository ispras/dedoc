import json
import math
import os
from collections import namedtuple
from typing import List, Tuple

import cv2
import numpy as np

from dedoc.api.dedoc_api import config
from dedoc.utils.pdf_utils import get_page_image
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader

BboxWithConfsType = namedtuple("WordWithConf", ["start", "end", "bbox", "confs", "text_type"])
DETAILED_DEBUG = False


class TestWordExtraction(AbstractTestApiDocReader):
    output_path = os.path.join(config["path_debug"], "word_bbox_extraction")

    def __extract_conf_annotation(self, anns_conf: List[dict], ann_bbox: dict, text: str) -> List[float]:
        confs = []
        debug = []

        for ann_conf in anns_conf:
            b, e = max(ann_conf["start"], ann_bbox["start"]), min(ann_conf["end"], ann_bbox["end"])
            interval = e - b
            if interval > 0:
                confs.append(ann_conf["value"])
                debug.append({f"{ann_conf['value']}[{b}:{e}]": [
                    interval, f"bbox:[{ann_bbox['start']}:{ann_bbox['end']}], {text[ann_bbox['start']:ann_bbox['end']]}"]})

        if DETAILED_DEBUG:
            print(debug)

        return confs

    def __extract_texttype_annotation(self, anns_type: List[dict], ann_bbox: dict, text: str) -> str:
        debug = []
        text_type = "typewritten"
        for ann_type in anns_type:
            b, e = max(ann_type["start"], ann_bbox["start"]), min(ann_type["end"], ann_bbox["end"])
            interval = e - b
            if interval > 0:
                text_type = ann_type["value"]
                debug.append({f"{ann_type['value']}:{b}:{e}": [
                    interval, f"bbox:[{ann_bbox['start']}:{ann_bbox['end']}], {text[ann_bbox['start']:ann_bbox['end']]}"]})
        if DETAILED_DEBUG:
            print(debug)

        return text_type

    def __get_words_annotation(self, structure: dict) -> List[BboxWithConfsType]:
        stack = [structure]
        words_annotation = []

        while len(stack) > 0:
            node = stack.pop()

            anns_bbox = [annotation for annotation in node["annotations"] if annotation["name"] == "bounding box"]
            anns_conf = [annotation for annotation in node["annotations"] if annotation["name"] == "confidence"]
            anns_type = [annotation for annotation in node["annotations"] if annotation["name"] == "text_type"]
            for ann_bbox in anns_bbox:
                # searching conf texttype values of word

                confs = self.__extract_conf_annotation(anns_conf, ann_bbox, node["text"])
                text_type = self.__extract_texttype_annotation(anns_type, ann_bbox, node["text"])

                words_annotation.append(BboxWithConfsType(start=ann_bbox["start"], end=ann_bbox["end"], bbox=ann_bbox["value"], confs=confs,
                                                          text_type=text_type))

            stack.extend(node["subparagraphs"])

        return words_annotation

    def __normalize_font_thickness(self, image: np.ndarray) -> Tuple[float, int]:
        FONT_SCALE = 6e-4
        THICKNESS_SCALE = 1e-3
        height, width, _ = image.shape
        font_scale = min(width, height) * FONT_SCALE
        thickness = math.ceil(min(width, height) * THICKNESS_SCALE)

        return font_scale, thickness

    def __draw_word_annotations(self, image: np.ndarray, word_annotations: List[BboxWithConfsType]) -> np.ndarray:

        font_scale, thickness = self.__normalize_font_thickness(image)
        page_height, page_width, *_ = image.shape
        for ann in word_annotations:
            bbox = json.loads(ann.bbox)
            p1 = (int(bbox["x_top_left"] * page_width), int(bbox["y_top_left"] * page_height))
            p2 = (int((bbox["x_top_left"] + bbox["width"]) * page_width), int((bbox["y_top_left"] + bbox["height"]) * page_height))
            cv2.rectangle(image, p1, p2, (0, 255, 0) if ann.text_type == "typewritten" else (255, 0, 0))
            text = ",".join(ann.confs) if ann.confs != [] else "None"
            cv2.putText(image, text, (int(bbox["x_top_left"] * page_width), int(bbox["y_top_left"] * page_height)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
        return image

    def test_pdfminer_document(self):
        output_path = os.path.join(self.output_path, "pdfminer_reader")
        os.makedirs(output_path, exist_ok=True)
        file_name = "pdf_with_text_layer/english_doc.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="true"))
        structure = result["content"]["structure"]
        word_annotations = self.__get_words_annotation(structure)
        image = np.asarray(get_page_image(self._get_abs_path(file_name), 0))
        image = self.__draw_word_annotations(image, word_annotations)
        cv2.imwrite(os.path.join(output_path, f"{os.path.split(file_name)[1]}.png"), image)

    def test_tabby_document(self):
        output_path = os.path.join(self.output_path, "tabby_reader")
        os.makedirs(output_path, exist_ok=True)
        file_name = "pdf_with_text_layer/english_doc.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        structure = result["content"]["structure"]
        word_annotations = self.__get_words_annotation(structure)
        image = np.asarray(get_page_image(self._get_abs_path(file_name), 0))

        image = self.__draw_word_annotations(image, word_annotations)
        cv2.imwrite(os.path.join(output_path, f"{os.path.split(file_name)[1]}.png"), image)
