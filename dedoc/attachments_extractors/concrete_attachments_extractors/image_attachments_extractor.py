from __future__ import annotations  # keep `torch` out of module import: Tensor below is only a type hint

import os
import uuid
from typing import Dict, Iterable, List, Optional

from dedocutils.data_structures.bbox import BBox
from numpy import ndarray

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile


class _RTDetrOutputs:
    """Minimal stand-in for the HF model output so ``post_process_object_detection`` (reads .logits / .pred_boxes)
    works with the tensors returned by the OpenVINO forward."""

    def __init__(self, logits: "Tensor", pred_boxes: "Tensor") -> None:
        self.logits = logits
        self.pred_boxes = pred_boxes


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
        self._device = None
        self._cpu_fwd = None        # OpenVINO CPU forward (pixel_values -> logits, pred_boxes); None -> torch fallback
        self._cpu_fwd_tried = False

        model_path = os.path.join(get_config()["resources_path"], "layout_model")
        if os.path.exists(model_path):
            self._model_name = model_path
            self.logger.info("Using locally saved layout analysis model")
        else:
            self._model_name = "docling-project/docling-layout-heron"
            self.logger.info("Layout analysis model will be loaded from huggingface")
        self._threshold = self.config.get("image_detection_threshold", 0.7)

    def _ensure_processor(self) -> None:
        if self._image_processor is None:
            from transformers import RTDetrImageProcessor
            self._image_processor = RTDetrImageProcessor.from_pretrained(self._model_name)

    def _ensure_model(self):
        import torch
        if self._model is None:
            from transformers import RTDetrV2ForObjectDetection
            self._device = "cuda:0" if self.config.get("on_gpu", False) and torch.cuda.is_available() else "cpu"
            self._model = RTDetrV2ForObjectDetection.from_pretrained(self._model_name).to(self._device).eval()
            self.logger.info(f"Layout analysis model is set to device {self._device}")
        return self._model

    @property
    def cpu_forward(self):
        """OpenVINO **CPU** forward for RT-DETR: ``pixel_values(N,3,640,640) float32 -> (logits, pred_boxes)``.

        The layout transformer's torch/onnxruntime CPU forward is ~2 s/page and the biggest CPU cost of the staged
        pipeline; OpenVINO runs the same graph ~1.35x faster on an Intel CPU. Returns ``None`` (torch fallback) when
        OpenVINO is absent. The ONNX graph is exported once (atomic) into resources/; after that a CPU worker never
        loads the ~230 MB torch model at all -- only the lightweight image processor, needed for pre/post-processing.
        """
        if self._cpu_fwd_tried:
            return self._cpu_fwd
        self._cpu_fwd_tried = True
        self._cpu_fwd = None
        try:
            from dedoc.utils.openvino_backend import compile_cpu_model, openvino_available
            if not openvino_available():  # layout's only fallback is torch, which needs no ONNX -> don't export for nothing
                return None
            ov_run = compile_cpu_model(self._ensure_onnx())
            if ov_run is not None:
                self._cpu_fwd = lambda pixel_values: ov_run({"pixel_values": pixel_values})  # [logits, pred_boxes]
        except Exception as e:
            self.logger.warning(f"OpenVINO layout accelerator unavailable ({e}); using torch on CPU")
            self._cpu_fwd = None
        return self._cpu_fwd

    def _ensure_onnx(self) -> str:
        from dedoc.config import get_config
        from dedoc.utils.openvino_backend import export_once
        onnx_path = os.path.join(get_config()["resources_path"], "layout_rtdetr.onnx")
        # export_once serializes across workers: only one loads the ~230 MB torch model to export (see its docstring)
        return export_once(onnx_path, self._export_onnx)

    def _export_onnx(self, onnx_path: str) -> None:
        import warnings
        import torch
        model = self._ensure_model()

        class _Wrap(torch.nn.Module):  # HF returns a dataclass; ONNX export needs plain tensor outputs
            def __init__(self, m: "torch.nn.Module") -> None:
                super().__init__()
                self.m = m

            def forward(self, pixel_values: "Tensor"):
                out = self.m(pixel_values=pixel_values)
                return out.logits, out.pred_boxes

        tmp_path = f"{onnx_path}.{os.getpid()}.tmp"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            torch.onnx.export(_Wrap(model).eval(), (torch.randn(1, 3, 640, 640),), tmp_path,
                              input_names=["pixel_values"], output_names=["logits", "pred_boxes"],
                              dynamic_axes={"pixel_values": {0: "n"}, "logits": {0: "n"}, "pred_boxes": {0: "n"}}, opset_version=17)
        os.replace(tmp_path, onnx_path)  # atomic: other workers see either no file or the complete one
        self.logger.info(f"Layout model exported to {onnx_path}")

    def _predict_batch(self, images: List[ndarray]) -> Iterable[Dict[str, Tensor]]:
        """Run RT-DETR layout detection on a batch of images in a single forward pass (OpenVINO on CPU, else torch)."""
        import torch

        self._ensure_processor()
        inputs = self._image_processor(images=list(images), return_tensors="pt")
        target_sizes = torch.tensor([image.shape[:-1] for image in images])

        on_gpu = self.config.get("on_gpu", False) and torch.cuda.is_available()
        cpu_forward = None if on_gpu else self.cpu_forward
        if cpu_forward is not None:
            import numpy as np
            logits, boxes = cpu_forward(np.ascontiguousarray(inputs["pixel_values"].numpy(), dtype=np.float32))
            outputs = _RTDetrOutputs(torch.from_numpy(np.asarray(logits)), torch.from_numpy(np.asarray(boxes)))
        else:
            self._ensure_model()
            inputs = inputs.to(self._device)
            target_sizes = target_sizes.to(self._device)
            with torch.no_grad():
                outputs = self._model(**inputs)

        return self._image_processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=self._threshold)

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given image using a document layout analysis method https://huggingface.co/docling-project/docling-layout-heron.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about the methods' parameters.
        """
        import cv2
        import os
        from dedoc.utils.parameter_utils import get_param_attachments_dir

        parameters = {} if parameters is None else parameters
        tmpdir, filename = os.path.split(file_path)
        attachments_dir = get_param_attachments_dir(parameters, tmpdir)
        image = cv2.imread(file_path)
        prediction = list(self._predict_batch([image]))[0]
        return self._attachments_from_prediction(image, prediction, attachments_dir, filename, parameters)

    def extract_batch(self, images: List[ndarray], attachments_dir: str, parameters: Optional[dict] = None) -> List[List[AttachedFile]]:
        """Detect attachments on a batch of page images with a single RT-DETR forward pass (one list per image)."""
        parameters = {} if parameters is None else parameters
        predictions = self._predict_batch(images)
        return [self._attachments_from_prediction(image, prediction, attachments_dir, "attachment.png", parameters)
                for image, prediction in zip(images, predictions)]

    def _attachments_from_prediction(self, image: ndarray, prediction: Dict[str, Tensor], attachments_dir: str,
                                     filename: str, parameters: dict) -> List[AttachedFile]:
        import cv2
        import os
        from dedoc.utils.parameter_utils import get_param_need_content_analysis
        from dedoc.utils.utils import get_unique_name
        from dedoc.readers.pdf_reader.data_classes.tables.location import Location
        from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment

        attachments = []
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
            cv2.imwrite(tmp_file_path, part)

            attachments.append(PdfImageAttachment(
                original_name=tmp_file_name,
                tmp_file_path=tmp_file_path,
                need_content_analysis=get_param_need_content_analysis(parameters),
                uid=f"attach_{uuid.uuid4()}",
                location=image_location
            ))

        return attachments
