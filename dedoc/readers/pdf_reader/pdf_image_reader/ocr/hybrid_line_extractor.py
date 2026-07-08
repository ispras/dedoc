"""
Hybrid OCR line extractor: PP-OCR / DBNet **detector** + PP-OCRv5 East-Slavic **recognizer**, both on
RapidOCR / ONNXRuntime-CUDA (no PyTorch in the recognition path).

Selected by ``config["ocr_engine"] = "hybrid"``; produces the same ``PageWithBBox`` structure as the other
extractors. The detector is exposed as separable parts so the staged pipeline can run each on its best resource:

    preprocess(image) -> prepro                [CPU: resize/normalize the page for DBNet]
    infer(prepro)     -> heatmap               [GPU: DBNet ONNX forward]
    postprocess(...)  -> boxes                 [CPU: DBPostProcess -> line boxes]
    recognize_detections(image, boxes) -> [(box, text, conf)]  [GPU: PP-OCRv5 CRNN ONNX on per-box crops]

``split_image2lines`` runs all parts in one call (used when OCR is a single stage). onnxruntime-gpu's cuDNN-9/CUDA-12
DLLs are added to the search path lazily.
"""
import logging
import threading
from typing import List, Tuple

import numpy as np

from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.data_classes.word_with_bbox import WordWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.easyocr_line_extractor import EasyOCRLineExtractor, _map_languages


def _det_preprocess(image: np.ndarray, det_max_side: int = 960, limit_side_len: int = 736,
                    mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)) -> np.ndarray:
    """Standalone reimplementation of RapidOCR's ``DetPreProcess`` (config: limit_type='min', limit_side_len=736,
    mean/std=0.5) so the CPU workers can run detection preprocessing WITHOUT loading RapidOCR/onnxruntime. Resizes
    to a multiple of 32, normalizes, CHW.

    ``det_max_side`` (px): DOWNSCALE so the long side <= it (limit_type='max'). DBNet detects fine at ~960 px and
    recognition still crops from the full-res image, so this shrinks the float preprocess (and its transport) with no
    effect on recognized text (default 960). ``det_max_side<=0`` -> original full-res 'min' behavior."""
    import cv2

    h, w = image.shape[:2]
    if det_max_side and det_max_side > 0:  # limit_type='max': downscale so the long side <= det_max_side
        ratio = (det_max_side / max(h, w)) if max(h, w) > det_max_side else 1.0
    else:  # original limit_type='min': upscale so the short side >= limit_side_len (full res for large scans)
        ratio = (limit_side_len / min(h, w)) if min(h, w) < limit_side_len else 1.0
    resize_h = int(round(int(h * ratio) / 32) * 32)
    resize_w = int(round(int(w * ratio) / 32) * 32)
    img = cv2.resize(image, (resize_w, resize_h))
    img = (img.astype("float32") * (1 / 255.0) - np.array(mean)) / np.array(std)
    return np.expand_dims(img.transpose((2, 0, 1)), axis=0).astype(np.float32)


def _rotate_crop(img: np.ndarray, box) -> np.ndarray:
    """Perspective-crop a 4-point detection box to an upright line image (PaddleOCR get_rotate_crop_image).

    cv2.warpPerspective's cost scales with the SOURCE image size, not the (small) output, so warping the full page
    once per box costs ~20 ms/box (~1.8 s/page). We first slice the box's axis-aligned bounding region (+2 px margin
    so INTER_CUBIC still samples real neighbours at the edges) and warp only that -> ~1 ms/box, identical output."""
    import cv2

    pts = np.array(box, dtype=np.float32)
    w = int(max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3])))
    h = int(max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])))
    if w <= 0 or h <= 0:
        return np.zeros((0, 0, 3), dtype=img.dtype)
    ix0, iy0 = max(int(pts[:, 0].min()) - 2, 0), max(int(pts[:, 1].min()) - 2, 0)
    src = img[iy0:int(np.ceil(pts[:, 1].max())) + 2, ix0:int(np.ceil(pts[:, 0].max())) + 2]
    if src.size == 0:
        return np.zeros((0, 0, 3), dtype=img.dtype)
    p = (pts - [ix0, iy0]).astype(np.float32)
    dst = cv2.warpPerspective(src, cv2.getPerspectiveTransform(p, np.float32([[0, 0], [w, 0], [w, h], [0, h]])),
                              (w, h), borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_CUBIC)
    return np.rot90(dst) if dst.shape[0] * 1.0 / max(dst.shape[1], 1) >= 1.5 else dst


def _setup_onnxruntime_cuda_dlls() -> None:
    import os
    import torch

    os.environ.pop("CUDA_PATH", None)
    site_packages = os.path.dirname(os.path.dirname(torch.__file__))
    for d in [os.path.join(os.path.dirname(torch.__file__), "lib"),
              os.path.join(site_packages, "nvidia", "cudnn", "bin"),
              os.path.join(site_packages, "nvidia", "cublas", "bin")]:
        if os.path.isdir(d):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


_LAT2CYR = {"A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К", "M": "М", "O": "О", "P": "Р",
            "T": "Т", "X": "Х", "Y": "У", "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х",
            "y": "у", "k": "к", "m": "м"}
_LAT_FOREIGN = set("DdFfGgIiJjLlNnQqRrSsUuVvWwZz")  # Latin letters with NO Cyrillic look-alike → genuine Latin marker
_CYR = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def _homoglyph(text: str) -> str:
    """Post-OCR Latin→Cyrillic homoglyph fix (Russian only): the recognizer sometimes emits a Latin look-alike for a
    Cyrillic letter (e.g. С→'C', О→'O'). Convert a token's Latin homoglyphs to Cyrillic UNLESS the token is a genuine
    Latin word — i.e. it has a foreign-only Latin letter (b, d, f, g, ...) and no Cyrillic (keeps 'Pentium', 'SQL')."""
    out = []
    for tok in text.split():
        if any(c in _LAT_FOREIGN for c in tok) and not any(c in _CYR for c in tok.lower()):
            out.append(tok)
        else:
            out.append("".join(_LAT2CYR.get(c, c) for c in tok))
    return " ".join(out)


class HybridOCRLineExtractor:

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self._det = None        # RapidOCR TextDetector (preprocess/infer/postprocess)
        self._ppocr_rec = None       # PP-OCRv5 East-Slavic recognizer (ONNX)
        self._tess_local = threading.local()  # per-thread Tesseract layout API (PyTessBaseAPI is not thread-safe)

    def _ensure_det(self):
        if self._det is None:
            _setup_onnxruntime_cuda_dlls()
            from rapidocr_onnxruntime import RapidOCR
            gpu = bool(self.config.get("on_gpu", False))
            self._det = RapidOCR(det_use_cuda=gpu).text_det
            self.logger.info(f"Hybrid OCR detector ready (PP-OCR, cuda={gpu})")
        return self._det

    def _ensure_ppocr_rec(self):
        if self._ppocr_rec is None:
            import os
            import onnxruntime as ort
            _setup_onnxruntime_cuda_dlls()
            from rapidocr_onnxruntime.ch_ppocr_rec.text_recognize import TextRecognizer
            model_dir = os.path.join(os.path.dirname(__file__), "ppocr_eslav")
            gpu = bool(self.config.get("on_gpu", False))
            model = "rec_fp16.onnx" if gpu else "rec.onnx"  # fp16 on GPU: ~same accuracy, ~30% faster; fp32 on CPU
            model_path = os.path.join(model_dir, model)
            self._ppocr_rec = TextRecognizer({
                "model_path": model_path, "use_cuda": gpu, "use_dml": False,
                "rec_keys_path": os.path.join(model_dir, "dict.txt"), "rec_batch_num": 8, "rec_img_shape": [3, 48, 320]})
            if gpu:
                # RapidOCR hardcodes cudnn_conv_algo_search=EXHAUSTIVE, which re-benchmarks conv algorithms for EVERY
                # unique crop width -> ~9 s/page on variable-width document lines. Rebuild the CUDA session with
                # HEURISTIC (pick an algorithm without the per-shape benchmark) -> ~40x faster recognition.
                so = ort.SessionOptions()
                so.log_severity_level = 4
                so.enable_cpu_mem_arena = False
                so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                cuda_opts = {"device_id": 0, "cudnn_conv_algo_search": "HEURISTIC"}
                self._ppocr_rec.session.session = ort.InferenceSession(
                    model_path, sess_options=so, providers=[("CUDAExecutionProvider", cuda_opts), "CPUExecutionProvider"])
            self.logger.info(f"Hybrid OCR recognizer ready (PP-OCRv5 East-Slavic {model}, cuda={gpu})")
        return self._ppocr_rec

    def _ensure_tess(self):
        api = getattr(self._tess_local, "api", None)  # per-thread: the ocr stage runs in a parent thread pool
        if api is None:
            import os
            import shutil
            exe = shutil.which("tesseract")  # add the tesseract lib dir for DLL resolution (Windows: py>=3.8 ignores PATH)
            if exe and hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(os.path.dirname(exe))
                except Exception:
                    pass
            from tesserocr import PyTessBaseAPI
            path = os.environ.get("TESSDATA_PREFIX")
            api = PyTessBaseAPI(path=path, lang="eng") if path else PyTessBaseAPI(lang="eng")
            self._tess_local.api = api
        return api

    def _order_by_tess_blocks(self, detections, image: np.ndarray) -> list:
        """Use Tesseract's page-layout analysis (AnalyseLayout — segmentation only, NO recognition, Apache-2.0, ~0.3-0.7
        s/page CPU) to fix the hybrid's reading order on multi-block pages: partition the (eslav-recognized) detections
        into Tesseract's blocks IN READING ORDER, so line-grouping runs per block and multi-column/multi-block text is
        emitted in the right order. Returns the detections grouped by block (reading order); unassigned appended last."""
        import cv2
        from PIL import Image
        from tesserocr import RIL, iterate_level

        api = self._ensure_tess()
        api.SetImage(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
        api.AnalyseLayout()
        blocks = []
        it = api.GetIterator()
        if it is not None:
            for _ in iterate_level(it, RIL.BLOCK):
                try:
                    blocks.append(it.BoundingBox(RIL.BLOCK))  # (left, top, right, bottom), Tesseract reading order
                except Exception:
                    pass
        groups = [[] for _ in range(len(blocks) + 1)]  # +1 bucket for detections outside every block (appended last)
        for det in detections:
            box = np.array(det[0])
            cx, cy = box[:, 0].mean(), box[:, 1].mean()
            idx = len(blocks)
            for i, (left, top, right, bottom) in enumerate(blocks):
                if left <= cx <= right and top <= cy <= bottom:
                    idx = i
                    break
            groups[idx].append(det)
        return [g for g in groups if g]

    # ---- separable detector parts ----
    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        # standalone numpy preprocessing: no RapidOCR/onnxruntime needed on the CPU workers running this stage
        return _det_preprocess(image, self.config.get("hybrid_det_max_side", 960)), (image.shape[0], image.shape[1])

    def infer(self, prepro: np.ndarray) -> np.ndarray:
        return self._ensure_det().infer(prepro)[0]

    def postprocess(self, preds: np.ndarray, ori_shape: Tuple[int, int]) -> List[np.ndarray]:
        det = self._ensure_det()
        boxes, _ = det.postprocess_op(preds, ori_shape)
        return det.filter_tag_det_res(boxes, ori_shape)

    def page_from_detections(self, detections, image: np.ndarray, page_num: int) -> PageWithBBox:
        ocr_conf_threshold = self.config.get("ocr_conf_threshold", -1)
        extract_line_bbox = self.config.get("labeling_mode", False)
        height, width = image.shape[:2]
        ocr_lines = None
        if self.config.get("hybrid_reading_order") == "tesseract" and detections:
            # borrow Tesseract's block reading order (multi-block/column pages), then line-group within each block.
            # Falls back to naive on any failure (e.g. Windows tesserocr/torch DLL-load order) so OCR never breaks.
            try:
                ocr_lines = []
                for block_dets in self._order_by_tess_blocks(detections, image):
                    ocr_lines.extend(EasyOCRLineExtractor._detections_to_lines(block_dets, ocr_conf_threshold))
            except Exception as e:
                self.logger.warning(f"Tesseract reading-order failed ({e}); using naive order")
                ocr_lines = None
        if ocr_lines is None:  # naive: line-group across the whole page, top-to-bottom
            ocr_lines = EasyOCRLineExtractor._detections_to_lines(detections, ocr_conf_threshold)
        lines_with_bbox = []
        for line_num, line in enumerate(ocr_lines):
            words = [WordWithBBox(text=word.text, bbox=word.bbox) for word in line.words]
            annotations = line.get_annotations(width, height, extract_line_bbox)
            lines_with_bbox.append(TextWithBBox(words=words, page_num=page_num, bbox=line.bbox, line_num=line_num, annotations=annotations))
        filtered = [ln for ln in lines_with_bbox if 0.01 < ln.bbox.height / (ln.bbox.width + 1e-6) < 24]
        return PageWithBBox(page_num=page_num, bboxes=filtered, image=image)

    def recognize_detections(self, image: np.ndarray, boxes, language: str) -> list:
        """Recognize the detection boxes with the PP-OCRv5 East-Slavic recognizer (ONNX) and return RAW detections
        ``(box, text, conf)``. Line-grouping (``page_from_detections``) is deferred to the metadata stage. The
        Latin→Cyrillic look-alike post-fix runs for Russian unless ``config["hybrid_homoglyph_fix"]`` is False."""
        if boxes is None or len(boxes) == 0:
            return []
        pairs = [(box, _rotate_crop(image, box)) for box in boxes]
        pairs = [(b, c) for b, c in pairs if c.shape[0] > 0 and c.shape[1] > 0]
        if not pairs:
            return []
        res, _ = self._ensure_ppocr_rec()([c for _, c in pairs])
        dets = [(b, t, cf) for (b, _), (t, cf) in zip(pairs, res)]
        if self.config.get("hybrid_homoglyph_fix", True) and "ru" in _map_languages(language):
            dets = [(b, _homoglyph(t), cf) for b, t, cf in dets]
        return dets

    def recognize_boxes(self, image: np.ndarray, boxes, page_num: int, language: str) -> PageWithBBox:
        return self.page_from_detections(self.recognize_detections(image, boxes, language), image, page_num)

    # ---- single-stage fallback (all parts in one call) ----
    def split_image2lines(self, image: np.ndarray, page_num: int, language: str = "rus+eng", is_one_column_document: bool = True) -> PageWithBBox:
        prepro, ori = self.preprocess(image)
        boxes = self.postprocess(self.infer(prepro), ori)
        return self.recognize_boxes(image, boxes, page_num, language)
