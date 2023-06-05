import os
from collections import namedtuple
from typing import Any
import torch
from torchvision.transforms import ToTensor

from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.utils.image_utils import get_bbox_from_image

FontType = namedtuple("FontType", ["bold", "other"])


class FontTypeClassifier:
    labels_list = ["bold", "OTHER"]

    def __init__(self, model_path: str) -> None:
        super().__init__()
        self._model = None
        self.model_path = model_path

    @property
    def model(self) -> Any:
        if self._model is not None:
            return self._model

        if not os.path.isfile(self.model_path):
            out_dir, out_name = os.path.split(self.model_path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="font_classifier", hub_name="model.pth")

        with open(self.model_path, "rb") as file:
            self._model = torch.load(f=file).eval()
            self._model.requires_grad_(False)

        return self._model

    def predict_annotations(self, page: PageWithBBox) -> PageWithBBox:
        if len(page.bboxes) == 0:
            return page
        tensor_predictions = self._get_model_predictions(page)
        is_bold = ["bold" if p else "not_bold" for p in (tensor_predictions[:, 0] > 0.5)]
        is_other = ["other" if p else "not_other" for p in (tensor_predictions[:, 1] > 0.5)]
        font_type_predictions = [FontType(*_) for _ in zip(is_bold, is_other)]

        boxes_fonts = zip(page.bboxes, font_type_predictions)

        for bbox, font_type in boxes_fonts:
            if font_type.bold == "bold":
                bbox.annotations.append(BoldAnnotation(start=0, end=len(bbox.text), value="True"))

        return page

    @staticmethod
    def _page2tensor(page: PageWithBBox) -> torch.Tensor:
        if len(page.bboxes) == 0:
            return torch.zeros()
        to_tensor = ToTensor()
        images = (get_bbox_from_image(image=page.image, bbox=bbox.bbox) for bbox in page.bboxes)
        tensors = (to_tensor(image) for image in images)
        tensors_reshaped = [tensor.unsqueeze(0) for tensor in tensors]
        return torch.cat(tensors_reshaped, dim=0)

    def _get_model_predictions(self, page: PageWithBBox) -> torch.Tensor:
        tensor = self._page2tensor(page)
        with torch.no_grad():
            return self.model(tensor)
