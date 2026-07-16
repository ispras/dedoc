from __future__ import annotations

import logging
import os
import warnings
from os import path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from dedoc.download_models import download_from_hub

# torch / torchvision / the EfficientNet model are imported lazily (inside the methods that need them), NOT at module
# import. CPU-only pipeline workers construct this classifier only to call the all-cv2 ``preprocess_cpu`` (the GPU
# worker does the forward), so eagerly importing torch would waste ~0.4 GB of committed memory in every CPU worker.


class ColumnsOrientationClassifier(object):
    """
    Class Classifier for work with Orientation Network. This class set device,
    preprocessing (transform) input data, weights of model
    """
    def __init__(self, on_gpu: bool, checkpoint_path: Optional[str], *, config: dict) -> None:
        self.logger = config.get("logger", logging.getLogger())
        self._on_gpu = on_gpu
        self.checkpoint_path = path.abspath(checkpoint_path)
        self.classes = [1, 2, 0, 90, 180, 270]
        self._net = None
        self._device = None       # torch is imported lazily on first real use (net/device/predict), not at construction
        self._transform = None
        self.location = None
        self._onnx_session = None
        self._onnx_tried = False

    @property
    def device(self):
        if self._device is None:
            self._set_device(self._on_gpu)
        return self._device

    @property
    def transform(self):
        if self._transform is None:
            self._set_transform_image()
        return self._transform

    @property
    def net(self) -> ClassificationModelTorch:
        if self._net is None:
            _ = self.device  # set device + self.location before loading weights
            from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.model import ClassificationModelTorch
            net = ClassificationModelTorch(self.checkpoint_path)
            if self.checkpoint_path is not None:
                self._load_weights(net)
            self._net = net
        self._net.to(self.device)
        return self._net

    @property
    def onnx_session(self):
        """onnxruntime session used for the **CPU** forward (None if unavailable -> caller falls back to torch).

        This EfficientNet's torch CPU forward is ~2.4x slower than onnxruntime's on the same input (1844 -> 770 ms for
        one 1200x1200 page, single intra-op thread), and on a CPU-only staged pipeline the orientation forward is ~35%
        of all per-page stage time -- so off-GPU the forward goes through ONNX. The GPU path stays on torch/CUDA, which
        is already fast (~187 ms/page) and where the batched forward pays off.

        The graph is exported once next to the checkpoint and reused; the export is atomic, so concurrent workers never
        observe a half-written file. Once it exists, a CPU worker no longer needs torch for the forward at all.
        Threads are left at 1 by default: the pipeline gets its parallelism from the worker processes, and an intra-op
        team per worker would oversubscribe the machine (override with DEDOC_ORT_THREADS).
        """
        if self._onnx_tried:
            return self._onnx_session
        self._onnx_tried = True
        try:
            import onnxruntime
            onnx_path = os.path.splitext(self.checkpoint_path)[0] + ".onnx"
            if not path.isfile(onnx_path):
                self._export_onnx(onnx_path)
            options = onnxruntime.SessionOptions()
            options.intra_op_num_threads = int(os.environ.get("DEDOC_ORT_THREADS", "1"))
            self._onnx_session = onnxruntime.InferenceSession(onnx_path, options, providers=["CPUExecutionProvider"])
        except Exception as e:
            self.logger.warning(f"ONNX orientation forward unavailable ({e}); using torch on CPU")
            self._onnx_session = None
        return self._onnx_session

    def _export_onnx(self, onnx_path: str) -> None:
        import torch
        net = self.net
        net.eval()
        tmp_path = f"{onnx_path}.{os.getpid()}.tmp"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            torch.onnx.export(net, torch.randn(1, 3, 1200, 1200), tmp_path, input_names=["input"], output_names=["logits"],
                              dynamic_axes={"input": {0: "n"}, "logits": {0: "n"}}, opset_version=17)
        os.replace(tmp_path, onnx_path)  # atomic: other workers see either no file or the complete one
        self.logger.info(f"Orientation model exported to {onnx_path}")

    def _decode(self, outputs: np.ndarray) -> List[Tuple[int, int]]:
        """(N, 6) logits -> [(columns, angle)]: the first 2 classes are the column count, the last 4 the orientation."""
        columns = outputs[:, :2].argmax(1)
        orientation = outputs[:, 2:].argmax(1)
        return [(self.classes[int(columns[i])], self.classes[2 + int(orientation[i])]) for i in range(len(columns))]

    def _forward(self, batch) -> np.ndarray:
        """Forward a prepared (N, 3, 1200, 1200) NCHW batch normalized to [-1, 1] (numpy or torch) -> (N, 6) logits."""
        session = None if self._on_gpu else self.onnx_session
        if session is not None:
            array = batch.cpu().numpy() if hasattr(batch, "cpu") else batch
            return session.run(["logits"], {"input": np.ascontiguousarray(array, dtype=np.float32)})[0]

        import torch
        net = self.net
        net.eval()
        with torch.no_grad():
            tensor = batch if hasattr(batch, "to") else torch.from_numpy(batch)
            return net(tensor.to(self.device)).cpu().numpy()

    @staticmethod
    def my_resize(image: Image) -> Image:
        from torchvision.transforms.functional import resize
        max_dim = max(image.size)
        image1 = resize(image, size=[round(image.size[1] / max_dim * 1200), round(image.size[0] / max_dim * 1200)])
        white_image = Image.new(size=(1200, 1200), color=(255, 255, 255), mode="RGB")
        white_image.paste(image1)
        return white_image

    @staticmethod
    def preprocess_cpu(image: np.ndarray, size: int = 1200) -> np.ndarray:
        """CPU-side preprocessing (all-cv2/numpy, no torch): aspect-preserving resize so the long side is ``size``,
        white-pad to a ``size`` x ``size`` square, BGR->RGB. Returns a uint8 RGB canvas. Runs on the CPU workers so
        the GPU worker only does the forward (mirrors the det_pre split); the normalize to [-1, 1] is deferred to the
        GPU (see :meth:`predict_prepared`) so the transported array is cheap uint8. ~2.6x faster than the PIL path
        (``my_resize`` + ToTensor + Normalize). INTER_AREA matches PIL's antialiased downscale closely."""
        h, w = image.shape[:2]
        max_dim = max(h, w)
        new_h, new_w = round(h / max_dim * size), round(w / max_dim * size)
        canvas = np.full((size, size, 3), 255, dtype=np.uint8)
        canvas[:new_h, :new_w] = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

    def _set_device(self, on_gpu: bool) -> None:
        """
        Set device configuration
        """
        import torch
        if on_gpu and torch.cuda.is_available():
            self._device = torch.device("cuda:0")
            self.location = lambda storage, loc: storage.cuda()
        else:
            self._device = torch.device("cpu")
            self.location = "cpu"

        self.logger.warning(f"Classifier is set to device {self._device}")

    def _load_weights(self, net: ClassificationModelTorch) -> None:
        import torch
        if not path.isfile(self.checkpoint_path):
            from dedoc.config import get_config
            self.checkpoint_path = os.path.join(get_config()["resources_path"], "scan_orientation_efficient_net_b0.pth")
            download_from_hub(out_dir=os.path.dirname(os.path.abspath(self.checkpoint_path)),
                              out_name="scan_orientation_efficient_net_b0.pth",
                              repo_name="scan_orientation_efficient_net_b0",
                              hub_name="model.pth")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            net.load_state_dict(torch.load(self.checkpoint_path, map_location=self.location))
            self.logger.info(f"Weights were loaded from {self.checkpoint_path}")

    def save_weights(self, path_checkpoint: str) -> None:
        import torch
        torch.save(self.net.state_dict(), path_checkpoint)
        self.logger.info(f"Weights were saved into {path_checkpoint}")

    def _set_transform_image(self) -> None:
        """
        Set configuration preprocessing for input image
        """
        from torchvision import transforms
        self._transform = transforms.Compose([
            transforms.Lambda(self.my_resize),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def get_features(self, image: np.array) -> "torch.Tensor":
        """
        Get features for the image
        """
        image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(np.uint8(image)).convert("RGB")
        tensor_image = self.transform(pil_image).unsqueeze(0).float().to(self.device)
        return tensor_image

    def predict(self, image: np.ndarray) -> Tuple[int, int]:
        """
        Predict class orientation of input image
        """
        return self._decode(self._forward(self.get_features(image)))[0]

    def predict_batch(self, images: List[np.ndarray]) -> List[Tuple[int, int]]:
        """
        Predict (columns, orientation) for a batch of images in a single forward pass.
        Equivalent to calling :meth:`predict` per image, but amortizes the model on the GPU.
        """
        if not images:
            return []

        import torch
        with torch.no_grad():
            batch = torch.cat([self.get_features(image) for image in images], dim=0)  # (N, 3, 1200, 1200)
        return self._decode(self._forward(batch))

    def predict_prepared(self, canvases: List[np.ndarray]) -> List[Tuple[int, int]]:
        """Forward + decode for pre-processed uint8 RGB canvases (from :meth:`preprocess_cpu`). Equivalent to
        :meth:`predict_batch` but with the (heavy) resize/pad already done off this worker.

        On GPU the normalize (ToTensor + Normalize -> [-1, 1]) runs on the device, so the CPU workers only hand over
        cheap uint8 arrays. On CPU the forward goes through onnxruntime (see :attr:`onnx_session`) and the normalize is
        done in numpy, which keeps torch out of the CPU workers entirely.
        """
        if not canvases:
            return []

        if not self._on_gpu and self.onnx_session is not None:
            batch = np.stack(canvases).transpose(0, 3, 1, 2).astype(np.float32) / 127.5 - 1.0  # == (x/255 - .5)/.5
            return self._decode(self._forward(batch))

        import torch
        with torch.no_grad():
            batch = torch.from_numpy(np.stack(canvases)).to(self.device)          # (N, H, W, 3) uint8
            batch = batch.permute(0, 3, 1, 2).float().div_(255).sub_(0.5).div_(0.5)  # NCHW, [0,255] -> [-1, 1]
            return self._decode(self._forward(batch))
