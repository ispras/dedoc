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

    def __extract_conf_annotation(self, anns_conf: List[dict], ann_bbox: dict, text: str) -> List[float]:
        confs = []
        debug = []

        for ann_conf in anns_conf:
            b, e = max(ann_conf["start"], ann_bbox["start"]), min(ann_conf["end"], ann_bbox["end"])
            interval = e - b
            if interval > 0:
                confs.append(ann_conf["value"])
                debug.append(
                    {
                        f"{ann_conf['value']}[{b}:{e}]": [
                            interval, f"bbox:[{ann_bbox['start']}:{ann_bbox['end']}], {text[ann_bbox['start']:ann_bbox['end']]}"
                        ]
                    }
                )

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
                debug.append(
                    {
                        f"{ann_type['value']}:{b}:{e}": [
                            interval, f"bbox:[{ann_bbox['start']}:{ann_bbox['end']}], {text[ann_bbox['start']:ann_bbox['end']]}"
                        ]
                    }
                )
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

                words_annotation.append(
                    BboxWithConfsType(start=ann_bbox["start"], end=ann_bbox["end"], bbox=ann_bbox["value"], confs=confs, text_type=text_type)
                )

            stack.extend(node["subparagraphs"])

        return words_annotation

    def __get_words_annotation_from_cell(self, table: dict) -> List[BboxWithConfsType]:
        words_annotation = []

        cells = []
        for row in table["cells"]:
            for cell in row:
                cells.append(cell)
                for line in cell["lines"]:
                    anns_bbox = [annotation for annotation in line["annotations"] if annotation["name"] == "bounding box"]
                    anns_conf = [annotation for annotation in line["annotations"] if annotation["name"] == "confidence"]
                    for ann_bbox in anns_bbox:
                        confs = self.__extract_conf_annotation(anns_conf, ann_bbox, line["text"])
                        words_annotation.append(BboxWithConfsType(start=ann_bbox["start"], end=ann_bbox["end"], bbox=ann_bbox["value"], confs=confs,
                                                                  text_type="typewritten"))
        return words_annotation

    def __normalize_font_thickness(self, image: np.ndarray) -> Tuple[float, int]:
        font_scale = 6e-4
        thickness_scale = 1e-3
        height, width, _ = image.shape
        font = min(width, height) * font_scale
        thickness = math.ceil(min(width, height) * thickness_scale)

        return font, thickness

    def __rotate_coordinate(self, x: int, y: int, xc: float, yc: float, angle: float) -> Tuple[int, int]:
        rad = angle * math.pi / 180
        x_rotated = int(float(x - xc) * math.cos(rad) - float(y - yc) * math.sin(rad) + xc)
        y_rotated = int(float(y - yc) * math.cos(rad) + float(x - xc) * math.sin(rad) + yc)

        return x_rotated, y_rotated

    def __draw_word_annotations(self, image: np.ndarray, word_annotations: List[BboxWithConfsType], angle: float = 0.) -> np.ndarray:

        font_scale, thickness = self.__normalize_font_thickness(image)
        x_c = image.shape[1] / 2
        y_c = image.shape[0] / 2

        for ann in word_annotations:
            bbox = json.loads(ann.bbox)
            p1 = (int(bbox["x_top_left"] * bbox["page_width"]), int(bbox["y_top_left"] * bbox["page_height"]))
            p2 = (int((bbox["x_top_left"] + bbox["width"]) * bbox["page_width"]), int((bbox["y_top_left"] + bbox["height"]) * bbox["page_height"]))

            if angle != 0.0:
                p1 = self.__rotate_coordinate(p1[0], p1[1], x_c, y_c, angle)
                p2 = self.__rotate_coordinate(p2[0], p2[1], x_c, y_c, angle)

            cv2.rectangle(image, p1, p2, (0, 255, 0) if ann.text_type == "typewritten" else (255, 0, 0))
            text = ",".join(ann.confs) if ann.confs != [] else "None"
            cv2.putText(
                image, text, (int(bbox["x_top_left"] * bbox["page_width"]), int(bbox["y_top_left"] * bbox["page_height"])), cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, (0, 0, 255), thickness
            )
        return image

    def __draw_tables_words(self, tables: List[dict], image: np.ndarray) -> np.ndarray:
        for table in tables:
            table_angle = table["metadata"]["rotated_angle"]

            word_annotations = self.__get_words_annotation_from_cell(table)
            image = self.__draw_word_annotations(image, word_annotations, angle=table_angle)
        return image

    def test_pdf_documents(self) -> None:
        filename_parameters_outputdir = [
            ["pdf_with_text_layer/english_doc.pdf", dict(pdf_with_text_layer="true"), "pdfminer_reader"],
            ["pdf_with_text_layer/english_doc.pdf", dict(pdf_with_text_layer="tabby"), "tabby_reader"]
        ]

        for file_name, parameters, outputdir in filename_parameters_outputdir:
            output_path = os.path.join(self.output_path, outputdir)
            os.makedirs(output_path, exist_ok=True)
            result = self._send_request(file_name, data=parameters)
            structure = result["content"]["structure"]
            word_annotations = self.__get_words_annotation(structure)
            image = np.asarray(get_page_image(self._get_abs_path(file_name), 0))
            ann = word_annotations[0]
            if ann is not None:
                bbox = json.loads(ann.bbox)
                image = cv2.resize(image, dsize=(bbox["page_width"], bbox["page_height"]), interpolation=cv2.INTER_CUBIC)
            image = self.__draw_word_annotations(image, word_annotations)
            tables = result["content"]["tables"]
            if len(tables) > 0:
                image = self.__draw_tables_words(tables, image)
            cv2.imwrite(os.path.join(output_path, f"{os.path.split(file_name)[1]}.png"), image)

    def test_table_word_extraction(self) -> None:
        output_path = os.path.join(self.output_path, "tables")
        os.makedirs(output_path, exist_ok=True)
        file_names = [
            "tables/example_with_table5.png", "tables/example_with_table3.png", "tables/example_with_table4.jpg", "tables/example_with_table6.png",
            "tables/example_with_table_horizontal_union.jpg", "scanned/orient_1.png", "tables/rotated_table.png"
        ]

        for file_name in file_names:
            result = self._send_request(file_name, data=dict())
            page_angle = result["metadata"]["other_fields"]["rotated_page_angles"][0]

            image = cv2.imread(self._get_abs_path(file_name))
            image = rotate_image(image, page_angle)

            # draw boxes of content's words
            structure = result["content"]["structure"]
            word_annotations = self.__get_words_annotation(structure)
            image = self.__draw_word_annotations(image, word_annotations)

            # draw boxes of table's words
            tables = result["content"]["tables"]
            if len(tables) > 0:
                image = self.__draw_tables_words(tables, image)

            cv2.imwrite(os.path.join(output_path, file_name.split("/")[-1]), image)

    def test_document_table_split_last_column(self) -> None:
        filename_to_parameters = {
            f"plat_por/plat_por_png ({i}).png": {
                "table_type": "split_last_column+wo_external_bounds",
                "need_text_localization": "False",
                "language": "rus",
                "is_one_column_document": "true",
                "document_orientation": "no_change"
            } for i in range(9)
        }
        output_path = os.path.join(self.output_path, "tables")
        os.makedirs(output_path, exist_ok=True)
        for filename, parameters in filename_to_parameters.items():
            result = self._send_request(file_name=filename, data=parameters, expected_code=200)
            structure = result["content"]["structure"]
            word_annotations = self.__get_words_annotation(structure)
            image = cv2.imread(self._get_abs_path(filename))
            image = rotate_image(image, result["metadata"]["other_fields"].get("rotated_page_angles", [0.])[0])
            image = self.__draw_word_annotations(image, word_annotations)
            tables = result["content"]["tables"]
            if len(tables) > 0:
                image = self.__draw_tables_words(tables, image)
            cv2.imwrite(os.path.join(output_path, filename.split("/")[-1]), image)
