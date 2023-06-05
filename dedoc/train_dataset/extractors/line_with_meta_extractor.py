import json
import os
from collections import defaultdict
from typing import List

import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from tqdm import tqdm

from dedoc.data_structures.bbox import BBox
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.html_reader.html_reader import HtmlReader
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.metadata_extractor import LineMetadataExtractor
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.train_dataset.data_structures.images_archive import ImagesArchive
from dedoc.train_dataset.data_structures.line_with_label import LineWithLabel


class LineWithMetaExtractor:

    def __init__(self, path: str, documents_path: str, *, config: dict) -> None:
        """
        create LineWithLabel from documents and labeled tasks
        @param path: path to file with labels
        @param documents_path: path to original documents
        @param config:
        """
        self.documents_path = documents_path
        self.path = path
        self.docx_reader = DocxReader(config=config)
        self.txt_reader = RawTextReader(config=config)
        self.html_reader = HtmlReader(config=config)
        self.metadata_extractor = LineMetadataExtractor(config={})

    def create_task(self) -> List[LineWithLabel]:
        with open(self.path) as file:
            dataset = json.load(file)
        grouped_dataset = defaultdict(list)
        for task in dataset.values():
            group = self._get_original_document(task)
            grouped_dataset[group].append(task)
        result = []
        for document_name, labels in tqdm(grouped_dataset.items()):
            if os.path.isfile(os.path.join(self.documents_path, document_name)):
                result += self._get_lines(document_name=document_name, labels=labels)
            else:
                print("Skip {}".format(document_name))  # noqa
        return result

    def _get_lines(self, document_name: str, labels: List[dict]) -> List[LineWithLabel]:
        if document_name.endswith((".png", ".pdf", ".zip")):
            return self._lines_from_image(document_name, labels)
        if document_name.endswith((".docx", ".txt", ".html")):
            if document_name.endswith(".docx"):
                reader = self.docx_reader
            elif document_name.endswith(".txt"):
                reader = self.txt_reader
            elif document_name.endswith(".html"):
                reader = self.html_reader
            else:
                raise Exception("Unknown document type {}".format(document_name))
            document = reader.read(os.path.join(self.documents_path, document_name), parameters={})
            lines = document.lines
            return self.__add_labels(document_name, labels, lines)

    def __add_labels(self, document_name: str, labels: List[dict], lines: List[LineWithMeta]) -> List[LineWithLabel]:
        label_dict = {
            data["data"]["_uid"]: data["labeled"][0] for data in labels
        }
        result = []
        for line in lines:
            if line.uid in label_dict:
                line_with_label = LineWithLabel(
                    uid=line.uid,
                    line=line.line,
                    metadata=line.metadata,
                    annotations=line.annotations,
                    label=label_dict[line.uid],
                    group=document_name)
                result.append(line_with_label)
        return result

    def _get_original_document(self, task: dict) -> str:
        return task["data"]["original_document"]

    def __create_bbox(self, data: dict) -> TextWithBBox:
        bbox = BBox(
            x_top_left=data["data"]["bbox"]["bbox"]["x_top_left"],
            y_top_left=data["data"]["bbox"]["bbox"]["y_top_left"],
            width=data["data"]["bbox"]["bbox"]["width"],
            height=data["data"]["bbox"]["bbox"]["height"]
        )
        return TextWithBBox(
            bbox=bbox,
            page_num=data["data"]["bbox"]["page_num"],
            text=data["data"]["bbox"]["text"],
            line_num=data["data"]["bbox"]["line_num"],
            uid=data["data"]["bbox"]["uid"]
        )

    def _lines_from_image(self, document_name: str, labels: List[dict]) -> List[LineWithLabel]:

        group_by_page_num = defaultdict(list)
        bboxes = [self.__create_bbox(data) for data in labels]
        for bbox in bboxes:
            group_by_page_num[bbox.page_num].append(bbox)

        result = []
        for page_num, bboxes in group_by_page_num.items():
            path = os.path.join(self.documents_path, document_name)
            if document_name.endswith(".png"):
                image = Image.open(path)
            elif path.endswith(".zip"):
                image = ImagesArchive(path).get_page(page_num)
            else:
                image = convert_from_path(path, first_page=page_num + 1, last_page=page_num + 2)[0]

            page_with_bboxes = PageWithBBox(
                image=np.array(image),
                page_num=page_num,
                bboxes=bboxes
            )
            label_dict = {
                data["data"]["_uid"]: data["labeled"][0] for data in labels
            }

            lines = self.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page_with_bboxes)
            for line in lines:
                if line.uid in label_dict:
                    line_with_label = LineWithLabel(
                        line=line.line,
                        metadata=line.metadata,
                        annotations=line.annotations,
                        label=label_dict[line.uid],
                        group=document_name,
                        uid=line.uid
                    )
                    result.append(line_with_label)
                else:
                    print("unknown line {}".format(line.uid))  # noqa
        return result
