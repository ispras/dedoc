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


def _order_points_clockwise(pts: np.ndarray) -> np.ndarray:
    """TL,TR,BR,BL ordering (RapidOCR TextDetector.order_points_clockwise) for the standalone box post-processing."""
    x = pts[np.argsort(pts[:, 0]), :]
    left = x[:2][np.argsort(x[:2, 1])]
    right = x[2:][np.argsort(x[2:, 1])]
    (tl, bl), (tr, br) = left, right
    return np.array([tl, tr, br, bl], dtype="float32")


def _min_area_box(contour):
    """DBPostProcess.get_mini_boxes: min-area rotated rectangle of a contour, points ordered TL,TR,BR,BL."""
    import cv2
    bb = cv2.minAreaRect(contour)
    pts = sorted(list(cv2.boxPoints(bb)), key=lambda p: p[0])
    i1, i4 = (0, 1) if pts[1][1] > pts[0][1] else (1, 0)
    i2, i3 = (2, 3) if pts[3][1] > pts[2][1] else (3, 2)
    return np.array([pts[i1], pts[i2], pts[i3], pts[i4]], dtype=np.float32), min(bb[1])


def _box_score_fast(bitmap: np.ndarray, _box: np.ndarray) -> float:
    """DBPostProcess.box_score_fast: mean heatmap value inside the box (fill a local mask, cv2.mean)."""
    import cv2
    h, w = bitmap.shape[:2]
    box = _box.copy()
    xmin = int(np.clip(np.floor(box[:, 0].min()), 0, w - 1)); xmax = int(np.clip(np.ceil(box[:, 0].max()), 0, w - 1))
    ymin = int(np.clip(np.floor(box[:, 1].min()), 0, h - 1)); ymax = int(np.clip(np.ceil(box[:, 1].max()), 0, h - 1))
    mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
    box[:, 0] -= xmin; box[:, 1] -= ymin
    cv2.fillPoly(mask, box.reshape(1, -1, 2).astype(np.int32), 1)
    return cv2.mean(bitmap[ymin:ymax + 1, xmin:xmax + 1], mask)[0]


def _unclip_boxes(boxes: np.ndarray, ratio: float = 1.6):
    """VECTORIZED closed-form replacement for DBPostProcess.unclip + get_mini_boxes. Every input box is a min-area
    RECTANGLE, so 'offset outward by D=Area*ratio/Perimeter (round joins) then re-fit min-area rect' reduces to
    'grow the rectangle by D on each side' -- pure arithmetic on all boxes at once (no per-box shapely+pyclipper).
    Matches the pyclipper path to <2 px (which washes out at the final int scaling). Returns (expanded, min_side)."""
    c = boxes.mean(1)                                                   # (N,2) centers
    e01, e03 = boxes[:, 1] - boxes[:, 0], boxes[:, 3] - boxes[:, 0]     # width / height edges
    w = np.linalg.norm(e01, axis=1); h = np.linalg.norm(e03, axis=1)
    area = 0.5 * np.abs((boxes[:, :, 0] * np.roll(boxes[:, :, 1], -1, 1) - boxes[:, :, 1] * np.roll(boxes[:, :, 0], -1, 1)).sum(1))
    perim = np.linalg.norm(boxes - np.roll(boxes, -1, 1), axis=2).sum(1)
    d = area * ratio / np.maximum(perim, 1e-6)
    u = e01 / np.maximum(w, 1e-6)[:, None]; v = e03 / np.maximum(h, 1e-6)[:, None]
    hw = (w / 2 + d)[:, None]; hh = (h / 2 + d)[:, None]
    corners = np.stack([c - hw * u - hh * v, c + hw * u - hh * v, c + hw * u + hh * v, c - hw * u + hh * v], 1)
    return corners.astype(np.float32), np.minimum(w + 2 * d, h + 2 * d)


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

    def forward_gpu(self, xt):  # xt: (N,3,48,W) GPU float32 -> GPU logits tensor (no sync, no download)
        import torch.nn.functional as F
        w = xt.shape[3]
        if w < self.min_w or w > self.max_w:
            xt = F.interpolate(xt, size=(48, min(max(w, self.min_w), self.max_w)), mode="bilinear", align_corners=False)
        xt = xt.contiguous()
        self.ctx.set_input_shape(self.in_name, tuple(xt.shape))
        self.ctx.set_tensor_address(self.in_name, xt.data_ptr())
        ot = self._torch.empty(tuple(self.ctx.get_tensor_shape(self.out_name)), dtype=self.odtype, device="cuda")
        self.ctx.set_tensor_address(self.out_name, ot.data_ptr())
        self.ctx.execute_async_v3(self._torch.cuda.current_stream().cuda_stream)
        return ot


class _TRTDet:
    """Standalone TensorRT runtime for the DBNet detector (dynamic 1x3xHxW input, [32,960] per side) -- mirrors
    _TRTRec. ``forward_gpu(xt)`` takes an on-device tensor and returns the on-device probability heatmap (pairs with
    ``infer_gpu_from_image`` for a fully GPU-resident detector); ``__call__`` accepts a numpy tensor (the CPU-preprocess
    path). Post-processing uses the standalone ``postprocess_cpu`` (no onnxruntime detector loaded at all)."""

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
        self.odtype = {trt.DataType.FLOAT: torch.float32, trt.DataType.HALF: torch.float16}[self.engine.get_tensor_dtype(self.out_name)]
        prof = self.engine.get_tensor_profile_shape(self.in_name, 0)  # (min, opt, max)
        self.max_h, self.max_w = prof[2][2], prof[2][3]

    def forward_gpu(self, xt):  # xt: (1,3,H,W) GPU float32 -> GPU heatmap (1,1,H,W)
        xt = xt.contiguous()
        self.ctx.set_input_shape(self.in_name, tuple(xt.shape))
        self.ctx.set_tensor_address(self.in_name, xt.data_ptr())
        ot = self._torch.empty(tuple(self.ctx.get_tensor_shape(self.out_name)), dtype=self.odtype, device="cuda")
        self.ctx.set_tensor_address(self.out_name, ot.data_ptr())
        self.ctx.execute_async_v3(self._torch.cuda.current_stream().cuda_stream)
        return ot

    def __call__(self, x):  # x: numpy (1,3,H,W) float32 -> [heatmap numpy], matching OrtInferSession.__call__
        torch = self._torch
        ot = self.forward_gpu(torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).cuda())
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


def _gpu_native_crop(page, box, h_img, w_img):
    """GPU equivalent of _rotate_crop: bilinear-sample the (perspective) quad out of the on-device page to native
    (h,w) via grid_sample, then rot90 if the box is tall (h/w>=1.5). Returns a (3,H',W') CUDA float tensor or None."""
    import torch
    import torch.nn.functional as F
    p = np.asarray(box, dtype=np.float32)  # TL,TR,BR,BL
    w = int(max(np.linalg.norm(p[0] - p[1]), np.linalg.norm(p[2] - p[3])))
    h = int(max(np.linalg.norm(p[0] - p[3]), np.linalg.norm(p[1] - p[2])))
    if w <= 0 or h <= 0:
        return None
    # sample at u=j/w, v=i/h (NOT j/(w-1)) to match cv2.warpPerspective's dst-rect [0,w]x[0,h] convention -- the last
    # column lands at (w-1)/w, not 1.0. Cuts the native-crop MAE vs warpPerspective from ~16.7 to ~2.1 (median ~0);
    # negligible for wide boxes but decisive for the tiny tall boxes that dominate table stacks.
    u = torch.arange(w, device="cuda").float() / w; v = torch.arange(h, device="cuda").float() / h
    vv, uu = torch.meshgrid(v, u, indexing="ij")
    c = torch.tensor(p, device="cuda"); tl, tr, br, bl = c[0], c[1], c[2], c[3]
    top = tl + uu[..., None] * (tr - tl)
    bot = bl + uu[..., None] * (br - bl)
    pts = top + vv[..., None] * (bot - top)  # (h,w,2) input pixel coords
    gx = pts[..., 0] / (w_img - 1) * 2 - 1
    gy = pts[..., 1] / (h_img - 1) * 2 - 1
    # bicubic to match _rotate_crop's cv2.INTER_CUBIC (bilinear here costs ~0.5 word-bag F1 -- crops read blurrier)
    crop = F.grid_sample(page, torch.stack([gx, gy], -1)[None], mode="bicubic", padding_mode="border", align_corners=True)[0]
    if h / max(w, 1) >= 1.5:
        crop = torch.rot90(crop, 1, dims=(1, 2))
    return crop


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

    def _ensure_det_trt(self):
        """Standalone TensorRT DBNet engine (``det_fp16.trt``) when ``config['hybrid_det_engine']=='trt_fp16'`` and on
        GPU -- 2-2.5x faster than the onnxruntime CUDA forward, and no onnxruntime detector is loaded at all (box post
        uses ``postprocess_cpu``). Cached; ``None`` when unavailable (-> onnxruntime path). The engine's optimization
        profile caps each input side at 960, so it is only used when ``hybrid_det_max_side<=960``."""
        if getattr(self, "_det_trt", "unset") == "unset":
            import os
            engine = {"trt_fp16": "det_fp16.trt"}.get(self.config.get("hybrid_det_engine", "trt_fp16"))
            path = os.path.join(os.path.dirname(__file__), "ppocr_eslav", engine) if engine else None
            ok = bool(self.config.get("on_gpu") and path and os.path.exists(path)
                      and int(self.config.get("hybrid_det_max_side", 960)) <= 960)
            self._det_trt = _TRTDet(path) if ok else None
            if self._det_trt is not None:
                self.logger.info("Hybrid OCR detector ready (DBNet + standalone TensorRT det_fp16.trt)")
        return self._det_trt

    def infer(self, prepro: np.ndarray) -> np.ndarray:
        trt_det = self._ensure_det_trt()
        return trt_det(prepro)[0] if trt_det is not None else self._ensure_det().infer(prepro)[0]

    def postprocess(self, preds: np.ndarray, ori_shape: Tuple[int, int]) -> List[np.ndarray]:
        if self._ensure_det_trt() is not None:
            return self.postprocess_cpu(preds, ori_shape)  # standalone DBPostProcess (no onnxruntime detector loaded)
        det = self._ensure_det()
        boxes, _ = det.postprocess_op(preds, ori_shape)
        return det.filter_tag_det_res(boxes, ori_shape)

    def _ensure_det_post(self):
        """DBPostProcess (per-box shapely+pyclipper unclip), lazily built without loading the detector model. Used
        only as the ``DEDOC_VEC_UNCLIP=0`` fallback for A/B-ing the vectorized closed-form unclip."""
        if getattr(self, "_det_post", None) is None:
            from rapidocr_onnxruntime.ch_ppocr_det.utils import DBPostProcess
            self._det_post = DBPostProcess(thresh=0.3, box_thresh=0.5, max_candidates=1000,
                                           unclip_ratio=1.6, use_dilation=True, score_mode="fast")
        return self._det_post

    @staticmethod
    def _order_clip_filter(boxes, src_w: int, src_h: int) -> np.ndarray:
        """filter_tag_det_res: clockwise order + clip to the page + drop boxes with a side <= 3 px."""
        out = []
        for box in boxes:
            box = _order_points_clockwise(box)
            for pno in range(box.shape[0]):
                box[pno, 0] = int(min(max(box[pno, 0], 0), src_w - 1))
                box[pno, 1] = int(min(max(box[pno, 1], 0), src_h - 1))
            if int(np.linalg.norm(box[0] - box[1])) > 3 and int(np.linalg.norm(box[0] - box[3])) > 3:
                out.append(box)
        return np.array(out)

    def postprocess_cpu(self, preds: np.ndarray, ori_shape: Tuple[int, int]) -> List[np.ndarray]:
        """Standalone DBNet box post-processing WITHOUT loading the detector ONNX model (so it can run on the CPU
        workers), reimplementing DBPostProcess + filter_tag_det_res but with a **vectorized closed-form unclip** in
        place of the per-box shapely+pyclipper (~71x faster on that step, boxes match to <2 px). Params are RapidOCR's
        config.yaml defaults (thresh 0.3, box_thresh 0.5, unclip_ratio 1.6, use_dilation). DEDOC_VEC_UNCLIP=0 falls
        back to the shapely+pyclipper DBPostProcess (for A/B)."""
        import os
        import cv2
        src_h, src_w = ori_shape
        if os.environ.get("DEDOC_VEC_UNCLIP", "1") == "0":           # A/B fallback: per-box shapely+pyclipper unclip
            boxes, _ = self._ensure_det_post()(preds, ori_shape)
            return self._order_clip_filter(boxes, src_w, src_h)
        pred = preds[0, 0] if preds.ndim == 4 else preds[0]          # (H,W) probability heatmap
        height, width = pred.shape
        mask = cv2.dilate((pred > 0.3).astype(np.uint8), np.array([[1, 1], [1, 1]], dtype=np.uint8))
        contours = cv2.findContours(mask * 255, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
        minis = []
        for contour in contours[:1000]:                             # max_candidates
            box, sside = _min_area_box(contour)
            if sside < 3:                                           # min_size
                continue
            if _box_score_fast(pred, box.copy()) < 0.5:             # box_thresh
                continue
            minis.append(box)
        if not minis:
            return np.array([])
        expanded, sside = _unclip_boxes(np.stack(minis), 1.6)       # vectorized closed-form unclip
        expanded = expanded[sside >= 5]                             # min_size + 2
        if len(expanded) == 0:
            return np.array([])
        expanded[..., 0] = np.clip(np.round(expanded[..., 0] / width * src_w), 0, src_w)   # scale to the source page
        expanded[..., 1] = np.clip(np.round(expanded[..., 1] / height * src_h), 0, src_h)
        return self._order_clip_filter(expanded, src_w, src_h)

    def infer_gpu_from_image(self, image: np.ndarray):
        """Detection forward with GPU-side preprocessing: upload the page, resize + normalize on the GPU, and run DBNet
        on the on-device tensor -- no CPU det-preprocess (``_det_preprocess``), no 8 MB ``det_prepro`` transport, and no
        separate H2D upload of the float tensor. With the TensorRT DBNet engine the forward is fully GPU-resident
        (``_TRTDet.forward_gpu``); otherwise the onnxruntime CUDA session is fed via IOBinding. Returns
        ``(heatmap, ori_shape, page)`` -- the on-device full-res page tensor is handed to ``recognize_boxes_fused`` so
        recognition reuses it instead of re-uploading the page (saves the duplicate 26 MB H2D on the GPU worker)."""
        import torch
        import torch.nn.functional as F
        h_img, w_img = image.shape[:2]
        page = torch.from_numpy(np.ascontiguousarray(image)).cuda().permute(2, 0, 1).unsqueeze(0).float()  # 1,3,H,W BGR
        side = int(self.config.get("hybrid_det_max_side", 960))
        ratio = side / max(h_img, w_img) if (side > 0 and max(h_img, w_img) > side) else 1.0  # limit_type='max' downscale
        rh = max(32, int(round(int(h_img * ratio) / 32) * 32))
        rw = max(32, int(round(int(w_img * ratio) / 32) * 32))
        x = F.interpolate(page, size=(rh, rw), mode="bilinear", align_corners=False)
        x = (((x / 255.0) - 0.5) / 0.5).contiguous()  # normalize (mean/std 0.5), matches _det_preprocess
        trt_det = self._ensure_det_trt()
        if trt_det is not None:  # fully GPU-resident: TRT DBNet directly on the device tensor
            heatmap = trt_det.forward_gpu(x)
            torch.cuda.synchronize()
            return heatmap.float().cpu().numpy(), (h_img, w_img), page
        sess = self._ensure_det().infer.session  # onnxruntime CUDA session via IOBinding (no re-upload of x)
        if not hasattr(self, "_det_io_names"):
            self._det_io_names = (sess.get_inputs()[0].name, sess.get_outputs()[0].name)
        in_name, out_name = self._det_io_names
        io = sess.io_binding()
        io.bind_input(name=in_name, device_type="cuda", device_id=0, element_type=np.float32,
                      shape=tuple(x.shape), buffer_ptr=x.data_ptr())
        io.bind_output(out_name)
        torch.cuda.synchronize()  # the resize/normalize kernels must finish before ORT reads x (separate CUDA streams)
        sess.run_with_iobinding(io)
        return io.copy_outputs_to_cpu()[0], (h_img, w_img), page

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

    def recognize_boxes_fused(self, image: np.ndarray, boxes, language: str, page=None) -> list:
        """GPU-resident recognition (requires the _TRTRec engine): upload the page ONCE, extract+resize every crop on
        the GPU, run the TRT recognizer on the GPU tensor, argmax on the GPU, and download only the tiny index/prob
        arrays -> CTC decode. Keeping the crops and the CRNN logits on-device and collapsing the per-op syncs cuts ~1/3
        of the recognition CPU AND per-page latency vs crops_from_boxes + recognize_crops.

        Crops are the CPU pipeline's two-step resample (warpPerspective to the box's NATIVE size, then resize to 48xW)
        done as TWO BATCHED grid_samples instead of a python per-box loop: pass 1 samples each box's quad at its native
        (h,w) into the top-left of a shared (Hmax,Wmax) canvas; pass 2 resizes each box's own native sub-region to
        (48, wt). Matching the native intermediate (not a shared oversampled grid) is what keeps the output on the CPU
        reference's distribution -- word-bag F1 vs the text layer is 0.952, == the CPU path. Returns RAW (box,text,conf)."""
        import torch
        import torch.nn.functional as F
        if boxes is None or len(boxes) == 0:
            return []
        rec = self._ensure_ppocr_rec()
        trt, decode = rec.session, rec.postprocess_op
        chars = decode.character  # class index -> char (0 = CTC blank); the ONLY CTC step left on the CPU is the join
        H, W = image.shape[:2]
        if page is None:  # detection (infer_gpu_from_image) may hand us the already-uploaded page -> reuse it (no re-H2D)
            page = torch.from_numpy(np.ascontiguousarray(image)).cuda().permute(2, 0, 1).unsqueeze(0).float()  # 1,3,H,W BGR
        q = np.stack([np.asarray(b, dtype=np.float32) for b in boxes])  # (M,4,2) TL,TR,BR,BL
        w = np.maximum(np.linalg.norm(q[:, 0] - q[:, 1], axis=1), np.linalg.norm(q[:, 2] - q[:, 3], axis=1))
        h = np.maximum(np.linalg.norm(q[:, 0] - q[:, 3], axis=1), np.linalg.norm(q[:, 1] - q[:, 2], axis=1))
        valid = (w > 0) & (h > 0)
        tall = valid & (h / np.maximum(w, 1) >= 1.5)   # tall boxes need rot90 -> the per-box path
        wide = valid & ~tall
        wt = np.clip(np.round(48 * w / np.maximum(h, 1)).astype(int), trt.min_w, trt.max_w)  # 48xW target widths
        hin = np.clip(np.ceil(h).astype(int), 2, 160)                # native intermediate height (capped for canvas size)
        win = np.clip(np.ceil(w).astype(int), 2, trt.max_w)          # native intermediate width
        out = [None] * len(boxes)
        cn = torch.from_numpy(np.stack([q[..., 0] / (W - 1) * 2 - 1, q[..., 1] / (H - 1) * 2 - 1], -1)).cuda()  # corners [-1,1]

        def _run(crops, ks):  # crops: (N,3,48,W) fp32 for the TRT engine
            logits = trt.forward_gpu(crops.contiguous())
            idx = torch.argmax(logits, -1)                            # (N,T) best class per timestep -- GPU
            prob = logits.float().amax(-1)                            # (N,T) its probability (rec output is softmaxed)
            keep = idx != 0                                           # drop the CTC blank (class 0) -- GPU
            keep[:, 1:] &= idx[:, 1:] != idx[:, :-1]                  # collapse consecutive duplicates -- GPU
            conf = (prob * keep).sum(-1) / keep.sum(-1).clamp(min=1)  # mean prob of the survivors -- GPU
            idx_c = idx.cpu().numpy(); keep_c = keep.cpu().numpy(); conf_c = conf.cpu().numpy()
            for bi, k in enumerate(ks):  # CPU: only the index->char lookup + join is left of the CTC decode
                out[int(k)] = (boxes[int(k)], "".join([chars[t] for t in idx_c[bi][keep_c[bi]]]), float(conf_c[bi]))

        order = np.where(wide)[0]
        order = order[np.argsort(wt[order])]  # batch similar widths, like the rec
        for bs in range(0, len(order), 8):
            ks = order[bs:bs + 8]; N = len(ks)
            Hmax = int(hin[ks].max()); Wmax = int(win[ks].max()); Wb = int(max(trt.min_w, min(int(wt[ks].max()), trt.max_w)))
            hik = torch.from_numpy(hin[ks]).cuda().float(); wik = torch.from_numpy(win[ks]).cuda().float()
            wtk = torch.from_numpy(wt[ks]).cuda().float()
            c = cn[ks]; tl, tr, br, bl = c[:, 0], c[:, 1], c[:, 2], c[:, 3]
            # pass 1: quad -> native (hik,wik) in the top-left of a shared (Hmax,Wmax) canvas
            uu = torch.arange(Wmax, device="cuda").float()[None, :] / (wik[:, None] - 1).clamp(min=1)  # (N,Wmax)
            vv = torch.arange(Hmax, device="cuda").float()[None, :] / (hik[:, None] - 1).clamp(min=1)  # (N,Hmax)
            uu4 = uu[:, None, :, None]; vv4 = vv[:, :, None, None]
            top = tl[:, None, None, :] + uu4 * (tr - tl)[:, None, None, :]
            bot = bl[:, None, None, :] + uu4 * (br - bl)[:, None, None, :]
            pts1 = top + vv4 * (bot - top)                                      # (N,Hmax,Wmax,2)
            oob = (uu4[..., 0] > 1.0) | (vv4[..., 0] > 1.0)                      # outside each box's native region
            pts1 = torch.where(oob[..., None], torch.full_like(pts1, -2.0), pts1)
            canvas = F.grid_sample(page.expand(N, 3, H, W), pts1, mode="bicubic", padding_mode="border", align_corners=True)
            # pass 2: resize each box's own native (hik,wik) sub-region -> (48, Wb)
            src_r = torch.arange(48, device="cuda").float()[None, :] / 47.0 * (hik[:, None] - 1)       # (N,48)
            u2 = torch.arange(Wb, device="cuda").float()[None, :] / (wtk[:, None] - 1).clamp(min=1)    # (N,Wb)
            src_c = u2 * (wik[:, None] - 1)
            gy = (src_r / (Hmax - 1) * 2 - 1)[:, :, None].expand(N, 48, Wb)
            gx = (src_c / (Wmax - 1) * 2 - 1)[:, None, :].expand(N, 48, Wb)
            crops = F.grid_sample(canvas, torch.stack([gx, gy], -1), mode="bicubic", padding_mode="border", align_corners=True)
            crops = (crops.clamp(0, 255) / 255.0 - 0.5) / 0.5           # BGR /255, normalize to [-1,1] (matches resize_norm)
            crops = torch.where((u2 > 1.0)[:, None, None, :].expand(N, 3, 48, Wb), torch.zeros_like(crops), crops)  # zero pad cols
            _run(crops, ks)

        for k in np.where(tall)[0]:
            nc = _gpu_native_crop(page, boxes[int(k)], H, W)
            if nc is None:
                continue
            wi = max(trt.min_w, min(int(round(48 * nc.shape[2] / nc.shape[1])), trt.max_w))
            cc = F.interpolate(nc[None], size=(48, wi), mode="bicubic", align_corners=False)[0].clamp(0, 255)
            _run((((cc / 255.0 - 0.5) / 0.5)[None]), [k])

        dets = [r for r in out if r is not None]
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
