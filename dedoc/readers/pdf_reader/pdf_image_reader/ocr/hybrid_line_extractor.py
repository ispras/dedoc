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
    # floor to 32: a very elongated image (e.g. a tall narrow stack of table cells) can round the short side to 0
    resize_h = max(32, int(round(int(h * ratio) / 32) * 32))
    resize_w = max(32, int(round(int(w * ratio) / 32) * 32))
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


def _xy_cut_blocks(items, out: list, gap: float) -> None:
    """Recursive XY-cut over detection boxes (geometric reading order, ~O(n log n), no Tesseract). ``items`` are
    ``(x0, y0, x1, y1, det)`` tuples; leaf blocks are appended to ``out`` in reading order. At each step it finds the
    widest whitespace gap in x (column separator) and in y (row separator) and cuts on the larger one when it exceeds
    ``gap`` -- vertical is preferred on ties so multi-column text reads column-by-column (left->right), then
    top->bottom within each column. Below-threshold groups are emitted as a leaf block."""
    if len(items) <= 1:
        if items:
            out.append([it[4] for it in items])
        return

    def widest_gap(lo: int, hi: int):
        s = sorted(items, key=lambda it: it[lo])
        run_hi = s[0][hi]
        best_g, best_k = 0.0, -1
        for k in range(1, len(s)):
            g = s[k][lo] - run_hi
            if g > best_g:
                best_g, best_k = g, k
            if s[k][hi] > run_hi:
                run_hi = s[k][hi]
        return best_g, best_k, s

    # Vertical (column) cuts only: reading order only needs columns separated, then naive top-to-bottom within each.
    # Horizontal cuts would split single-column pages into bands -- no ordering benefit but +30% nodes and wall. A
    # full-width element (title/rule) covers the inter-column gap, so no vertical cut fires there and it stays one block
    # (naive), which is correct for a spanning element. So: recurse only while a real column gap exists.
    vg, vk, vs = widest_gap(0, 2)
    if vg > gap:
        _xy_cut_blocks(vs[:vk], out, gap)
        _xy_cut_blocks(vs[vk:], out, gap)
    else:
        out.append([it[4] for it in items])


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


class _TRTRec:
    """Standalone TensorRT runtime for the CRNN recognizer — 2-2.5x faster than the onnxruntime CUDA fp16 session.
    Bypasses the onnxruntime TensorRT EP (which fails to build this PaddlePaddle-exported model); the raw
    trt.Builder/OnnxParser build it fine. Loads a prebuilt serialized engine (``rec_fp16.trt`` / ``rec_int8.trt``);
    the input width is clamped to the engine's [48, 1600] optimization profile (very long lines are squished)."""

    def __init__(self, engine_path: str) -> None:
        import os
        import torch
        libs = os.path.join(os.path.dirname(os.path.dirname(torch.__file__)), "tensorrt_libs")
        if os.path.isdir(libs) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(libs)
        import tensorrt_bindings as trt
        self._torch, self._trt = torch, trt
        logger = trt.Logger(trt.Logger.ERROR)
        self.engine = trt.Runtime(logger).deserialize_cuda_engine(open(engine_path, "rb").read())
        self.ctx = self.engine.create_execution_context()
        self.in_name = self.out_name = None
        for i in range(self.engine.num_io_tensors):
            n = self.engine.get_tensor_name(i)
            setattr(self, "in_name" if self.engine.get_tensor_mode(n) == trt.TensorIOMode.INPUT else "out_name", n)
        self.odtype = {trt.DataType.FLOAT: torch.float32, trt.DataType.HALF: torch.float16,
                       trt.DataType.INT8: torch.int8, trt.DataType.INT32: torch.int32}[self.engine.get_tensor_dtype(self.out_name)]
        prof = self.engine.get_tensor_profile_shape(self.in_name, 0)  # (min, opt, max) — clamp to the engine's width range
        self.min_w, self.max_w = prof[0][3], prof[2][3]

    def __call__(self, x):  # x: (N,3,48,W) float32; returns [logits] to match OrtInferSession.__call__
        torch = self._torch
        xt = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda()
        w = xt.shape[3]
        if w < self.min_w or w > self.max_w:  # keep within the engine's optimization-profile width range
            xt = torch.nn.functional.interpolate(xt, size=(48, min(max(w, self.min_w), self.max_w)), mode="bilinear", align_corners=False).contiguous()
        self.ctx.set_input_shape(self.in_name, tuple(xt.shape))
        self.ctx.set_tensor_address(self.in_name, xt.data_ptr())
        ot = torch.empty(tuple(self.ctx.get_tensor_shape(self.out_name)), dtype=self.odtype, device="cuda")
        self.ctx.set_tensor_address(self.out_name, ot.data_ptr())
        self.ctx.execute_async_v3(torch.cuda.current_stream().cuda_stream)
        torch.cuda.synchronize()
        return [ot.float().cpu().numpy()]


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
            import onnxruntime as ort
            _setup_onnxruntime_cuda_dlls()
            from rapidocr_onnxruntime import RapidOCR
            gpu = bool(self.config.get("on_gpu", False))
            self._det = RapidOCR(det_use_cuda=gpu).text_det
            if gpu:
                # RapidOCR's CUDA detector session defaults to cudnn EXHAUSTIVE search + max cuDNN workspace +
                # kNextPowerOfTwo arena, which reserve GBs of committed GPU memory per worker. Rebuild it leaner
                # (HEURISTIC + exact-size arena + no max workspace) -> much lower memory and identical output; the
                # algorithm choice is a speed/memory knob only. Mirrors the recognizer session fix.
                so = ort.SessionOptions()
                so.log_severity_level = 4
                so.enable_cpu_mem_arena = False
                cuda_opts = {"device_id": 0, "arena_extend_strategy": "kSameAsRequested",
                             "cudnn_conv_algo_search": "HEURISTIC", "cudnn_conv_use_max_workspace": "0"}
                self._det.infer.session = ort.InferenceSession(
                    self._det.infer.session._model_path, sess_options=so,
                    providers=[("CUDAExecutionProvider", cuda_opts), "CPUExecutionProvider"])
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
            rec_engine = self.config.get("hybrid_rec_engine", "onnx")
            trt_file = {"trt_fp16": "rec_fp16.trt", "trt_int8": "rec_int8.trt"}.get(rec_engine)
            if gpu and trt_file and os.path.exists(os.path.join(model_dir, trt_file)):
                # standalone TensorRT engine (2-2.5x faster than the onnxruntime CUDA fp16 session); swaps the whole
                # callable session (TextRecognizer calls self.session(batch)[0]).
                self._ppocr_rec.session = _TRTRec(os.path.join(model_dir, trt_file))
                self.logger.info(f"Hybrid OCR recognizer ready (PP-OCRv5 East-Slavic + TensorRT {trt_file})")
            elif gpu:
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
            else:
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

    def _xy_cut_detection_blocks(self, detections) -> list:
        """Geometric reading order: partition detections into blocks via a recursive XY-cut (no Tesseract, ~free).
        Returns the detections grouped into blocks in reading order (column-by-column, top-to-bottom)."""
        items = []
        for d in detections:
            b = np.array(d[0])
            items.append((b[:, 0].min(), b[:, 1].min(), b[:, 0].max(), b[:, 1].max(), d))
        heights = sorted(it[3] - it[1] for it in items)
        # gap threshold = median line height x mult; 0.5 was best on gen_texts (long WER 0.69->0.41, short 0.41->0.19)
        gap = (heights[len(heights) // 2] or 1.0) * float(self.config.get("hybrid_xycut_mult", 0.5))
        out: list = []
        _xy_cut_blocks(items, out, gap)
        return out

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
        order = self.config.get("hybrid_reading_order", "geometric")
        if order in ("geometric", "tesseract") and detections:
            # Fix the reading order on multi-block/multi-column pages (naive top-to-bottom interleaves columns), then
            # line-group within each block. Cuts multi-block WER dramatically (gen_texts long: naive 0.69 -> 0.056,
            # ~= Tesseract) at zero recognition change (word-bag F1 unchanged) -- see COMPONENT_QUALITY_REPORT.md. No-op
            # on single-column text.
            #   "geometric" (DEFAULT): a recursive XY-cut over the detection boxes -- ~free (no extra model call).
            #   "tesseract": borrow Tesseract's layout blocks -- marginally better on complex layouts but +~0.4 s/page.
            # Both fall back to naive on any failure so OCR never breaks.
            try:
                blocks = self._xy_cut_detection_blocks(detections) if order == "geometric" else self._order_by_tess_blocks(detections, image)
                ocr_lines = []
                for block_dets in blocks:
                    ocr_lines.extend(EasyOCRLineExtractor._detections_to_lines(block_dets, ocr_conf_threshold))
            except Exception as e:
                self.logger.warning(f"{order} reading-order failed ({e}); using naive order")
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
        return self.recognize_crops(self.crops_from_boxes(image, boxes), language)

    def crops_from_boxes(self, image: np.ndarray, boxes) -> list:
        """CPU-only: rotate-crop each detection box out of the page image. Split from recognition so it can run on a
        CPU worker (it is ~65 ms/page of warpPerspective) instead of blocking the GPU worker (see TENSORRT_INT8.md)."""
        if boxes is None or len(boxes) == 0:
            return []
        pairs = [(box, _rotate_crop(image, box)) for box in boxes]
        return [(b, c) for b, c in pairs if c.shape[0] > 0 and c.shape[1] > 0]

    def recognize_crops(self, pairs: list, language: str) -> list:
        """GPU: run the recognizer on pre-extracted crops -> RAW detections (box, text, conf)."""
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
