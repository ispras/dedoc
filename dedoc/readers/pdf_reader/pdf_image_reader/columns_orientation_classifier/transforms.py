from typing import Any, Dict

import numpy as np
from PIL import Image
from torchvision import transforms

from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier


class ImageTransform(object):
    """
    Class transformation input Image before Network
    """

    def __init__(self) -> None:
        self.transform = transforms.Compose([
            transforms.Lambda(ColumnsOrientationClassifier.my_resize),
            transforms.CenterCrop(1200),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def __call__(self, image: np.ndarray) -> Image:
        pil_image = Image.fromarray(np.uint8(image)).convert("RGB")
        image = self.transform(pil_image)
        return image


class TransformWithLabels(object):
    """
    Class transformation input data [Image, label] before Network
    """

    def __init__(self) -> None:
        self.transform = transforms.Compose([
            transforms.Lambda(ColumnsOrientationClassifier.my_resize),
            transforms.CenterCrop(1200),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def __call__(self, sample: dict) -> Dict[str, Any]:
        image, orientation, columns = sample["image"], sample["orientation"], sample["columns"]
        pil_image = Image.fromarray(np.uint8(image)).convert("RGB")
        image = self.transform(pil_image)

        return {"image": image, "orientation": orientation, "columns": columns, "image_name": sample["image_name"]}
