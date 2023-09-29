import json
import math
import os
from collections import namedtuple
from typing import List, Tuple

import cv2
import numpy as np

from dedoc.api.dedoc_api import config
from dedoc.utils.image_utils import rotate_image
from dedoc.utils.pdf_utils import get_page_image
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader

BboxWithConfsType = namedtuple("WordWithConf", ["start", "end", "bbox", "confs", "text_type"])
DETAILED_DEBUG = False


class TestWordExtraction(AbstractTestApiDocReader):
    output_path = os.path.join(config["path_debug"], "word_bbox_extraction")

    def extract_conf_annotation(self, anns_conf: List[dict], ann_bbox: dict, text: str) -> List[float]:
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

    def extract_texttype_annotation(self, anns_type: List[dict], ann_bbox: dict, text: str) -> str:
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

    def get_words_annotation(self, structure: dict) -> List[BboxWithConfsType]:
        stack = [structure]
        words_annotation = []

        while len(stack) > 0:
            node = stack.pop()

            anns_bbox = [annotation for annotation in node["annotations"] if annotation["name"] == "bounding box"]
            anns_conf = [annotation for annotation in node["annotations"] if annotation["name"] == "confidence"]
            anns_type = [annotation for annotation in node["annotations"] if annotation["name"] == "text_type"]
            for ann_bbox in anns_bbox:
                # searching conf texttype values of word

                confs = self.extract_conf_annotation(anns_conf, ann_bbox, node["text"])
                text_type = self.extract_texttype_annotation(anns_type, ann_bbox, node["text"])

                words_annotation.append(BboxWithConfsType(start=ann_bbox["start"], end=ann_bbox["end"], bbox=ann_bbox["value"], confs=confs,
                                                          text_type=text_type))

            stack.extend(node["subparagraphs"])

        return words_annotation

    def get_words_annotation_from_cell(self, table: dict) -> List[BboxWithConfsType]:
        words_annotation = []

        cells = []
        for row in table["cells"]:
            for cell in row:
                cells.append(cell)
                for line in cell["lines"]:
                    anns_bbox = [annotation for annotation in line["annotations"] if annotation["name"] == "bounding box"]
                    anns_conf = [annotation for annotation in line["annotations"] if annotation["name"] == "confidence"]
                    for ann_bbox in anns_bbox:
                        confs = self.extract_conf_annotation(anns_conf, ann_bbox, line["text"])
                        words_annotation.append(BboxWithConfsType(start=ann_bbox["start"], end=ann_bbox["end"], bbox=ann_bbox["value"], confs=confs,
                                                                  text_type="typewritten"))
        return words_annotation

    def normalize_font_thickness(self, image: np.ndarray) -> Tuple[float, int]:
        FONT_SCALE = 6e-4
        THICKNESS_SCALE = 1e-3
        height, width, _ = image.shape
        font_scale = min(width, height) * FONT_SCALE
        thickness = math.ceil(min(width, height) * THICKNESS_SCALE)

        return font_scale, thickness

    def rotate_coordinate(self, x: int, y: int, xc: float, yc: float, angle: float) -> Tuple[int, int]:
        rad = angle * math.pi / 180
        x_rotated = int(float(x - xc) * math.cos(rad) - float(y - yc) * math.sin(rad) + xc)
        y_rotated = int(float(y - yc) * math.cos(rad) + float(x - xc) * math.sin(rad) + yc)

        return x_rotated, y_rotated

    def draw_word_annotations(self, image: np.ndarray, word_annotations: List[BboxWithConfsType], angle: float = 0.) -> np.ndarray:

        font_scale, thickness = self.normalize_font_thickness(image)
        x_c = image.shape[1] / 2
        y_c = image.shape[0] / 2

        for ann in word_annotations:
            bbox = json.loads(ann.bbox)
            p1 = (int(bbox["x_top_left"] * bbox["page_width"]), int(bbox["y_top_left"] * bbox["page_height"]))
            p2 = (int((bbox["x_top_left"] + bbox["width"]) * bbox["page_width"]), int((bbox["y_top_left"] + bbox["height"]) * bbox["page_height"]))

            if angle != 0.0:
                p1 = self.rotate_coordinate(p1[0], p1[1], x_c, y_c, angle)
                p2 = self.rotate_coordinate(p2[0], p2[1], x_c, y_c, angle)

            cv2.rectangle(image, p1, p2, (0, 255, 0) if ann.text_type == "typewritten" else (255, 0, 0))
            text = ",".join(ann.confs) if ann.confs != [] else "None"
            cv2.putText(image, text, (int(bbox["x_top_left"] * bbox["page_width"]), int(bbox["y_top_left"] * bbox["page_height"])),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
        return image

    def test_pdfminer_document(self):
        output_path = os.path.join(self.output_path, "pdfminer_reader")
        os.makedirs(output_path, exist_ok=True)
        file_name = "pdf_with_text_layer/english_doc.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="true"))
        structure = result["content"]["structure"]
        word_annotations = self.get_words_annotation(structure)
        image = np.asarray(get_page_image(self._get_abs_path(file_name), 0))
        image = self.draw_word_annotations(image, word_annotations)
        cv2.imwrite(os.path.join(output_path, f"{os.path.split(file_name)[1]}.png"), image)

    def test_tabby_document(self):
        output_path = os.path.join(self.output_path, "tabby_reader")
        os.makedirs(output_path, exist_ok=True)
        file_name = "pdf_with_text_layer/english_doc.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        structure = result["content"]["structure"]
        image = np.asarray(get_page_image(self._get_abs_path(file_name), 0))
        word_annotations = self.get_words_annotation(structure)
        ann = word_annotations[0]
        if ann is not None:
            bbox = json.loads(ann.bbox)
            image = cv2.resize(image, dsize=(bbox["page_width"], bbox["page_height"]), interpolation=cv2.INTER_CUBIC)

        image = self.draw_word_annotations(image, word_annotations)
        cv2.imwrite(os.path.join(output_path, f"{os.path.split(file_name)[1]}.png"), image)

    def test_table_word_extraction(self):
        output_path = os.path.join(self.output_path, 'tables')
        os.makedirs(output_path, exist_ok=True)
        file_names = ["tables/example_with_table5.png", "tables/example_with_table3.png", "tables/example_with_table4.jpg",
                      "tables/example_with_table6.png", "tables/example_with_table_horizontal_union.jpg",
                      "scanned/orient_1.png", "tables/rotated_table.png"]

        for file_name in file_names:
            result = self._send_request(file_name, data=dict())
            table0 = result["content"]["tables"][0]
            page_angle = result["metadata"]["other_fields"]["rotated_page_angles"][0]
            table_angle = table0["metadata"]["rotated_angle"]

            word_annotations = self.get_words_annotation_from_cell(table0)
            image = cv2.imread(self._get_abs_path(file_name))
            image = rotate_image(image, page_angle)

            image = self.draw_word_annotations(image, word_annotations, angle=table_angle)
            cv2.imwrite(os.path.join(output_path, file_name.split('/')[-1]), image)
