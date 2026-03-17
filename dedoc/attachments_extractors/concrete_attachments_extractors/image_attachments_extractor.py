import os
import uuid
from typing import Dict, Iterable, List, Optional

from dedocutils.data_structures.bbox import BBox
from numpy import ndarray
from torch import Tensor

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile


class ImageAttachmentsExtractor(AbstractAttachmentsExtractor):
    """
    Extract attachments from image files.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        from dedoc.config import get_config
        super().__init__(config=config, recognized_extensions=recognized_extensions.image_like_format, recognized_mimes=recognized_mimes.image_like_format)
        self._classes = {
            2,  # Formula
            6  # Picture
        }
        self._image_processor = None
        self._model = None

        model_path = os.path.join(get_config()["resources_path"], "layout_model")
        if os.path.exists(model_path):
            self._model_name = model_path
            self.logger.info("Using locally saved layout analysis model")
        else:
            self._model_name = "docling-project/docling-layout-heron"
            self.logger.info("Layout analysis model will be loaded from huggingface")
        self._threshold = self.config.get("image_detection_threshold", 0.7)

    def _predict(self, image: ndarray) -> Iterable[Dict[str, Tensor]]:
        import torch
        from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection

        if self._image_processor is None:
            self._image_processor = RTDetrImageProcessor.from_pretrained(self._model_name)

        if self._model is None:
            self._model = RTDetrV2ForObjectDetection.from_pretrained(self._model_name)

        inputs = self._image_processor(images=[image], return_tensors="pt")
        with torch.no_grad():
            outputs = self._model(**inputs)

        results = self._image_processor.post_process_object_detection(outputs, target_sizes=torch.tensor([image.shape[:-1]]), threshold=self._threshold)
        return results

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given image using a document layout analysis method https://huggingface.co/docling-project/docling-layout-heron.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about the methods' parameters.
        """
        import cv2
        import os
        from dedoc.utils.parameter_utils import get_param_need_content_analysis, get_param_attachments_dir
        from dedoc.utils.utils import get_unique_name
        from dedoc.readers.pdf_reader.data_classes.tables.location import Location
        from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment

        parameters = {} if parameters is None else parameters
        tmpdir, filename = os.path.split(file_path)
        attachments_dir = get_param_attachments_dir(parameters, tmpdir)
        attachments = []

        image = cv2.imread(file_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        predictions = self._predict(image)

        for prediction in predictions:
            for label_id, box in zip(prediction["labels"], prediction["boxes"]):
                if label_id.item() not in self._classes:
                    continue

                box = [round(i) for i in box.tolist()]
                x_top_left, x_bottom_right = max(0, box[0]), min(box[2], image.shape[1])
                y_top_left, y_bottom_right = max(0, box[1]), min(box[3], image.shape[0])
                part = image[y_top_left:y_bottom_right, x_top_left:x_bottom_right]
                image_location = Location(page_number=0, bbox=BBox.from_two_points((x_top_left, y_top_left), (x_bottom_right, y_bottom_right)))

                tmp_file_name = get_unique_name(filename)
                tmp_file_path = os.path.join(attachments_dir, tmp_file_name)
                cv2.imwrite(tmp_file_path, cv2.cvtColor(part, cv2.COLOR_RGB2BGR))

                image_attachment = PdfImageAttachment(
                    original_name=tmp_file_name,
                    tmp_file_path=tmp_file_path,
                    need_content_analysis=get_param_need_content_analysis(parameters),
                    uid=f"attach_{uuid.uuid4()}",
                    location=image_location
                )
                attachments.append(image_attachment)

        return attachments
