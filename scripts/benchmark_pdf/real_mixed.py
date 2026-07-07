import argparse
import json
import logging
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from dedocutils.data_structures import BBox
from numpy import ndarray
from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
from tqdm import tqdm
from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection

from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.onepage_table_extractor import \
    OnePageTableExtractor
from dedoc.utils.image_utils import fill_bbox_on_image

INTERESTING_KEYS = ["table", "image_table"]
PAGES_NUMBER = 100


class LayoutDetector:
    def __init__(self) -> None:
        self._classes = {
            6: "image",  # Picture
            8: "hard_table"  # Table
        }
        self._image_processor = None
        self._model = None
        self._model_name = "docling-project/docling-layout-heron"
        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self._image_processor = RTDetrImageProcessor.from_pretrained(self._model_name)
        self._model = RTDetrV2ForObjectDetection.from_pretrained(self._model_name).to(self._device).eval()
        self._threshold = 0.7

    def predict(self, images: list[ndarray]) -> list[tuple[list, list]]:
        inputs = self._image_processor(images=images, return_tensors="pt").to(self._device)
        with torch.no_grad():
            outputs = self._model(**inputs)

        target_sizes = torch.tensor([image.shape[:-1] for image in images], device=self._device)
        predictions = self._image_processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=self._threshold)

        results = []
        for prediction, image in zip(predictions, images):
            labels = []
            boxes = []

            for label_id, p_box in zip(prediction["labels"], prediction["boxes"]):
                if label_id.item() not in self._classes:
                    continue
                labels.append(self._classes[label_id.item()])

                box = [round(i) for i in p_box.tolist()]
                x_top_left, x_bottom_right = max(0, box[0]), min(box[2], image.shape[1])
                y_top_left, y_bottom_right = max(0, box[1]), min(box[3], image.shape[0])
                boxes.append(BBox.from_two_points((x_top_left, y_top_left), (x_bottom_right, y_bottom_right)))
            results.append((labels, boxes))
        return results


def convert_to_gray(image: ndarray) -> ndarray:
    import cv2
    import numpy as np

    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    if gray_image.mean() < 220:  # filter black and white image
        binary_mask = gray_image >= np.quantile(gray_image, 0.05)
        gray_image[binary_mask] = 255
    return gray_image


@dataclass
class DocPage:
    doc: str
    page_num: int
    classes: list[str]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir', type=Path)
    parser.add_argument('out_dir', type=Path)
    args = parser.parse_args()

    layout_detector = LayoutDetector()

    pages = []

    batch_size = 32
    for file_path in tqdm(args.in_dir.rglob('*.pdf')):
        images = convert_from_path(file_path)
        images = [cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB) for image in images]
        total_pages = len(images)
        for i in range(0, total_pages, batch_size):
            batch = images[i:i + batch_size]
            layout_predictions = layout_detector.predict(batch)
            for j, (image, layout_prediction) in enumerate(zip(batch, layout_predictions)):
                labels, boxes = layout_prediction
                table_extractor = OnePageTableExtractor(config={}, logger=logging.getLogger(__name__))
                for label, box in zip(labels, boxes):
                    if label == "image":
                        image = fill_bbox_on_image(image, box)
                try:
                    if i + j != 0:
                        tables = table_extractor.extract_onepage_tables_from_image(convert_to_gray(image), i + j, "rus+eng", "")
                    else:
                        tables = []
                except Exception as e:
                    print(e)
                    tables = []
                labels = set(labels)
                if tables:
                    labels.add("table")
                if labels:
                    pages.append(DocPage(doc=str(file_path), page_num=i + j, classes=list(labels)))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "pages.json", "w", encoding="utf-8") as f:
        pages_list = [page.__dict__ for page in pages]
        json.dump(pages_list, f, ensure_ascii=False, indent=2)

    pages_groups = defaultdict(list)

    for page in pages_list:
        doc_path = Path(page["doc"])
        classes = set(page["classes"])

        if classes == {"image"} and "image" in INTERESTING_KEYS:
            pages_groups["image"].append(page)

        if classes == {"table"} and "table" in INTERESTING_KEYS:
            pages_groups["table"].append(page)

        if classes == {"hard_table"} and "hard_table" in INTERESTING_KEYS:
            pages_groups["hard_table"].append(page)

        if classes == {"image", "table"} and "image_table" in INTERESTING_KEYS:
            pages_groups["image_table"].append(page)

        if classes == {"image", "hard_table"} and "image_hard_table" in INTERESTING_KEYS:
            pages_groups["image_hard_table"].append(page)

    for key in pages_groups:
        pages_num = len(pages_groups[key])
        print(f"{pages_num} pages {key}")

        pages_copies_num = PAGES_NUMBER - pages_num % PAGES_NUMBER
        pages_copies = deepcopy(pages_groups[key][:pages_copies_num])
        pages_groups[key].extend(pages_copies)

        group_pages = pages_groups[key]
        print(f"after copy: {len(group_pages)} pages {key}")

        group_out_dir = args.out_dir / key
        group_out_dir.mkdir(parents=True, exist_ok=True)
        reader = None
        prev_doc = None

        for i in range(0, len(group_pages), PAGES_NUMBER):
            batch = group_pages[i:i + PAGES_NUMBER]
            writer = PdfWriter()

            for page in batch:
                if page["doc"] != prev_doc:
                    print(page["doc"])
                    reader = PdfReader(page["doc"])
                    prev_doc = page["doc"]
                writer.add_page(reader.pages[page["page_num"]])

            output_path = group_out_dir / f"{i + 1}-{i + PAGES_NUMBER}.pdf"
            print(output_path)
            with output_path.open('wb') as out_f:
                writer.write(out_f)
