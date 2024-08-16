import inspect
import json
import os
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional

from dedocutils.data_structures import BBox
from tqdm import tqdm

import dedoc.data_structures.concrete_annotations
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.color_annotation import ColorAnnotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.utils.utils import similarity_levenshtein
from train_dataset.data_structures.line_with_label import LineWithLabel


class BaseGT(ABC):
    def __init__(self, labels_path: str, documents_path: str, logfile_dir: str) -> None:
        self.labels_path = labels_path
        self.documents_path = documents_path
        os.makedirs(logfile_dir, exist_ok=True)
        self.logfile = open(os.path.join(logfile_dir, "reload_labels.log"), "w")
        print(f"Logfile was created {os.path.join(logfile_dir, 'reload_labels.log')}")  # noqa

    def load_gt(self) -> List[List[LineWithLabel]]:
        with open(self.labels_path) as file:
            dataset = json.load(file)

        grouped_dataset = defaultdict(list)
        for task in dataset.values():
            group = task["data"]["original_document"]
            grouped_dataset[group].append(task)

        lines_with_labels = [self._get_lines(document_name=document_name, labels=labels) for document_name, labels in tqdm(grouped_dataset.items())]

        return lines_with_labels

    def __del__(self) -> None:
        self.logfile.close()

    @abstractmethod
    def _get_lines(self, document_name: str, labels: List[dict]) -> List[LineWithLabel]:
        pass


class LoadAndUpdateGTLineWithLabel(BaseGT):
    """
    Class
    * parses labels_path (GT file) extract text lines
    * parses all original documents using dedoc's readers (TXT (RawTextReader), DocxReader, HtmlReader and PDFReader)
    * update GT annotations of gt lines with the same line_uid (IT'S NOT IMPLEMENTED)
    """

    def __init__(self, labels_path: str, documents_path: str, parameters_path: str, logfile_dir: str, config: Optional[Dict] = None) -> None:
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_auto_reader import PdfAutoReader
        from dedoc.readers.docx_reader.docx_reader import DocxReader
        from dedoc.readers.html_reader.html_reader import HtmlReader
        super().__init__(labels_path, documents_path, logfile_dir)

        self.parameters = self.__init_parameters(parameters_path)

        if not config:
            config = {}

        self.docx_reader = DocxReader(config=config)
        self.txt_reader = RawTextReader(config=config)
        self.html_reader = HtmlReader(config=config)
        self.image_reader = PdfImageReader(config=config)
        self.pdf_reader = PdfAutoReader(config=config)

    def __init_parameters(self, parameters_path: str) -> Dict:
        if not os.path.isfile(parameters_path):
            return {}
        with open(parameters_path) as file:
            return json.load(file)

    def _get_lines(self, document_name: str, labels: List[dict]) -> List[LineWithLabel]:
        if document_name.endswith(".png"):
            reader = self.image_reader
        elif document_name.endswith(".pdf"):
            reader = self.pdf_reader
        elif document_name.endswith(".docx"):
            reader = self.docx_reader
        elif document_name.endswith(".txt"):
            reader = self.txt_reader
        elif document_name.endswith(".html"):
            reader = self.html_reader
        else:
            raise Exception(f"Unknown document type {document_name}")

        pages = set([label["data"]["_metadata"]["page_id"] for label in labels])
        start_page, end_page = min(pages), max(pages)
        self.parameters["pages"] = f"{start_page + 1}:{end_page + 1}"

        document = reader.read(os.path.join(self.documents_path, document_name), parameters=self.parameters)
        lines = document.lines
        return self.__add_labels(document_name, labels, lines)

    def __add_labels(self, document_name: str, labels: List[dict], lines: List[LineWithMeta]) -> List[LineWithLabel]:
        # search a similarity line in GT (for getting label)
        line_with_labels = []
        window = 50
        miss = 0
        time_b = time.time()

        for line_id, line in enumerate(lines):
            analyzed_labels = labels[max(line_id - window, 0):min(len(lines), line_id + window)]
            label = None
            for gt_line in analyzed_labels:
                if similarity_levenshtein(line.line, gt_line["data"]["_line"]) > 0.8:
                    label = gt_line["labeled"]
                    break

            if not label:
                self.logfile.write(f"Line uid={line.uid} with text={line.line} was not found in GT")
                miss += 1

            line_with_labels.append(LineWithLabel(line.line, line.metadata, line.annotations, label, document_name, line.uid))
        self.logfile.write(f"File {document_name}, Miss count % = {miss / len(lines)}, Update_labels_time = {time.time() - time_b} sec")
        self.logfile.flush()

        return line_with_labels


class LoadGTLineWithLabel(BaseGT):
    """The mode of GT loading when: GT' annotations are actual and fresh"""

    def __init__(self, labels_path: str, documents_path: str, logfile_dir: str) -> None:
        """
        create LineWithLabel from documents and labeled tasks
        @param path: path to file with labels
        @param documents_path: path to original documents
        @param config:
        """
        super().__init__(labels_path, documents_path, logfile_dir)

    def _get_lines(self, document_name: str, labels: List[dict]) -> List[LineWithLabel]:
        self.document_name = document_name
        lines = [self.__get_line_from_gt(label) for label in labels]
        lines = self.__add_labels(labels, lines)

        return lines

    def __get_line_from_gt(self, gt_line: dict) -> LineWithMeta:
        return LineWithMeta(
            line=gt_line["data"]["_line"],
            metadata=LineMetadata(page_id=gt_line["data"]["_metadata"]["page_id"],
                                  line_id=gt_line["data"]["_metadata"]["line_id"]),
            annotations=self.__load_annotations_from_gt(gt_line["data"]["_annotations"]),
            uid=gt_line["data"]["_uid"]
        )

    def __load_annotations_from_gt(self, gt_anns: List[Dict]) -> List[Annotation]:
        annotations = inspect.getmembers(dedoc.data_structures.concrete_annotations, lambda member: inspect.isclass(member))

        load_anns = []
        for gt_ann in gt_anns:
            ann = [ann for ann in annotations if gt_ann["name"] == ann[1].name and gt_ann["name"] not in ["attachment"]]

            if not ann:
                continue

            if gt_ann["name"] == BBoxAnnotation.name:
                try:
                    box, width, height = BBoxAnnotation.get_bbox_from_value(gt_ann["value"])
                    load_anns.append(ann[0][1](start=gt_ann["start"], end=gt_ann["end"], value=box, page_width=width, page_height=height))
                except Exception:
                    self.logfile.write(f"Exception: BBoxAnnotattion deprecates in GT. File={self.document_name}")
                    bbox_dict = json.loads(gt_ann["value"])
                    if all(key in bbox_dict for key in ("x_top_left", "y_top_left", "width", "height")):
                        bbox = BBox(x_top_left=bbox_dict["x_top_left"], y_top_left=bbox_dict["y_top_left"],
                                    width=bbox_dict["width"], height=bbox_dict["height"])
                        load_anns.append(ann[0][1](start=gt_ann["start"], end=gt_ann["end"], value=bbox, page_width=1.0, page_height=1.0))
                    else:
                        self.logfile.write(f"Exception: Couldn't load BBoxAnnotation's value={gt_ann['value']} from GT. File={self.document_name}")
            elif gt_ann["name"] == ColorAnnotation.name:
                try:
                    load_anns.append(ann[0][1](start=gt_ann["start"], end=gt_ann["end"], red=gt_ann["red"], green=gt_ann["green"], blue=gt_ann["blue"]))
                except Exception:
                    rgb_dict = json.loads(gt_ann["value"])
                    if all(key in rgb_dict for key in ("red", "green", "blue")):
                        load_anns.append(ann[0][1](
                            start=gt_ann["start"], end=gt_ann["end"], red=rgb_dict["red"], green=rgb_dict["green"], blue=rgb_dict["blue"])
                        )
                    else:
                        self.logfile.write(f"Exception: Couldn't load ColorAnnotation's value={gt_ann} from GT. File={self.document_name}")
            else:  # other annotations
                load_anns.append(ann[0][1](start=gt_ann["start"], end=gt_ann["end"], value=gt_ann["value"]))

        return load_anns

    def __add_labels(self, labels: List[dict], lines: List[LineWithMeta]) -> List[LineWithLabel]:
        gt_line_uid2label = {data["data"]["_uid"]: data["labeled"][0] for data in labels}
        line_with_labels = [
            LineWithLabel(line.line, line.metadata, line.annotations, gt_line_uid2label[line.uid], self.document_name, line.uid)
            for line in lines if line.uid in gt_line_uid2label
        ]

        return line_with_labels
