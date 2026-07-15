"""
Phase 2c: the PdfImageReader per-page pipeline decomposed into staged tasks (see ARCHITECTURE.md §9).

Each stage is a ``process(config, doc) -> doc`` handler that reads the fields it needs from the page
*document* (a dict) and augments it with its results. Big arrays (the page image) travel between processes
through shared memory; a skipped/failed stage simply passes the document through, so downstream stages read
defaults. All handlers reuse the helpers of a single :class:`PdfImageReader` built once per worker.
"""
from typing import Any, Dict, List, Optional

from dedoc.pipeline.executor import Handler
from dedoc.pipeline.stage import Resource
from dedoc.pipeline.task import ExecMode, TaskSpec

_READER = None  # a PdfImageReader whose helpers the handlers reuse (built once per process)


def _set_cuda_blocking_sync() -> None:
    # cudaDeviceScheduleBlockingSync (0x04): the CPU thread YIELDS while waiting for a GPU op instead of busy-spinning.
    # onnxruntime/TensorRT/torch default to spin, which burns a full core per GPU worker (measured: it was ~half the
    # GPU worker's CPU -- rec CPU 117 -> 56 ms/page). Must be set before the process's CUDA context is created.
    import ctypes
    import glob
    import os
    try:
        import torch
        dll = glob.glob(os.path.join(os.path.dirname(torch.__file__), "lib", "cudart64*.dll"))
        if dll:
            ctypes.CDLL(dll[0]).cudaSetDeviceFlags(0x04)
    except Exception:
        pass


def init_reader(config_overrides: Optional[dict] = None) -> Any:
    global _READER
    if _READER is None:
        import os
        from dedoc.config import get_config
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        # DEDOC_BLOCKING_SYNC (default off): frees the GPU worker's spin-wait CPU but ADDS per-op wake latency -- measured
        # a net loss in the pipeline (wall +9%), because the GPU worker's per-page latency, not its CPU-busy, is the
        # constraint. Kept as an off-by-default flag for re-measurement.
        if (config_overrides or {}).get("on_gpu") and os.environ.get("DEDOC_BLOCKING_SYNC") == "1":
            _set_cuda_blocking_sync()
        _READER = PdfImageReader(config={**get_config(), **(config_overrides or {})})
    return _READER


# ---------------------------------------------------------------- stage handlers

_PDF_CACHE: dict = {}  # per worker process: {path: PdfDocument}. Opened once (the 59 MB DAE re-read per page would


def _render_pdfium(path: str, page_number: int):
    """Render one page with pypdfium2 (Apache-2.0, PDFium) at 200 DPI -> BGR array. The PdfDocument is cached per
    worker process (opening the file per page would re-read the whole PDF). MUST run single-threaded per process:
    PDFium is not thread-safe, so this stage runs in the isolated worker processes (exec_mode THREAD), never the
    parent thread pool. The document is loaded from bytes (a path makes PDFium hold a Windows lock that collides with
    the pipeline temp-file cleanup)."""
    import numpy as np
    import pypdfium2 as pdfium

    pdf = _PDF_CACHE.get(path)
    if pdf is None:
        for old in list(_PDF_CACHE.values()):  # bound memory: only the current document stays cached
            try:
                old.close()
            except Exception:
                pass
        _PDF_CACHE.clear()
        with open(path, "rb") as f:
            pdf = pdfium.PdfDocument(f.read())
        _PDF_CACHE[path] = pdf
    page = pdf[page_number]
    bmp = page.render(scale=200 / 72)  # 200 DPI, matches pdf2image's default resolution
    arr = bmp.to_numpy()  # RGB(A); shares the bitmap buffer -> materialize the copy before closing
    arr = arr[:, :, :3] if (arr.ndim == 3 and arr.shape[2] == 4) else arr
    image = np.ascontiguousarray(arr[:, :, ::-1])  # RGB -> BGR
    bmp.close()  # pypdfium2 v5 enforces child-before-parent close; the cached document stays open
    page.close()
    # PDFium's glyph anti-aliasing renders text ~1px thinner than Poppler, which costs ~3.8% word-bag F1 on short-text
    # pages. A 2x2 erode thickens the dark glyphs back to Poppler weight and recovers that exactly (verified on
    # gen_texts short/long) at ~1 ms/page. See TENSORRT_INT8.md.
    import cv2
    return cv2.erode(image, np.ones((2, 2), np.uint8), iterations=1)


def _render(config: dict, doc: dict) -> dict:
    """Render this page's image on demand (lazy render): a PDF page -> bitmap, or load an image file.
    Uses pypdfium2 (~3x faster than pdf2image/pdftoppm at the same 200-DPI resolution/quality); falls back to
    pdf2image if pypdfium2 is missing or rejects the PDF. Output is BGR, matching PdfBaseReader._split_pdf2image."""
    import os
    import cv2
    import numpy as np
    from dedoc.extensions import recognized_mimes
    from dedoc.utils.utils import get_file_mime_type

    path, page_number = doc["path"], doc["page_number"]
    if get_file_mime_type(path) in recognized_mimes.pdf_like_format or path.lower().endswith(".pdf"):
        image = None
        if os.environ.get("DEDOC_RENDER", "pdfium") != "pdftoppm":
            try:
                image = _render_pdfium(path, page_number)
            except Exception:  # pypdfium2 missing, or PDFium (stricter than poppler) rejecting a PDF -> fall through
                image = None
        if image is None:
            from pdf2image import convert_from_path
            image = cv2.cvtColor(np.array(convert_from_path(path, first_page=page_number + 1, last_page=page_number + 1)[0]), cv2.COLOR_BGR2RGB)
    else:
        image = cv2.imread(path)
    return {**doc, "image": image}


def _binarize(config: dict, doc: dict) -> dict:
    image, _ = _READER.binarizer.preprocess(doc["image"])
    return {**doc, "image": image}


def _orient_pre(config: dict, doc: dict) -> dict:
    # CPU-side orientation preprocessing (resize/pad/BGR->RGB), split off the GPU worker like det_pre so the GPU stage
    # runs only the EfficientNet forward. Produces a uint8 RGB canvas transported via the shared-memory buffer pool.
    canvas = _READER.column_orientation_classifier.preprocess_cpu(doc["image"])
    return {**doc, "orient_prepro": canvas}


def _orient_predict(config: dict, doc: dict) -> dict:
    clf = _READER.column_orientation_classifier
    canvas = doc.get("orient_prepro")
    canvas = canvas if canvas is not None else clf.preprocess_cpu(doc["image"])
    columns, angle = clf.predict_prepared([canvas])[0]
    return {**{k: v for k, v in doc.items() if k != "orient_prepro"}, "columns": columns, "angle": angle}


def _orient_predict_batch(configs: List[dict], docs: List[dict]) -> List[dict]:
    # single forward pass over the whole batch; the resize/pad already ran on the CPU workers (orient_pre stage)
    clf = _READER.column_orientation_classifier
    canvases = [d["orient_prepro"] if "orient_prepro" in d else clf.preprocess_cpu(d["image"]) for d in docs]
    results = clf.predict_prepared(canvases)
    return [{**{k: v for k, v in doc.items() if k != "orient_prepro"}, "columns": columns, "angle": angle}
            for doc, (columns, angle) in zip(docs, results)]


_SKEW_MIN_SIDE = 1000  # refine (fine sweep) the skew on an image downscaled to this long side; never upscale a low-res page
_SKEW_COARSE_SIDE = 512  # the coarse GUESS runs on a smaller thumbnail (cheaper rotations); refined at _SKEW_MIN_SIDE
_SKEW_MAX_ANGLE = 45


def _detect_skew_angle(image) -> float:
    """
    Projection-profile fine-skew detection (same method as dedocutils SkewCorrector) but run on a **downscaled**
    image: estimating the angle does not need full resolution, and the original tried 91 full-page rotations per
    page (~1.25 s). Downscaling to ``_SKEW_MIN_SIDE`` (with a floor so an already-small page is not upscaled) gives
    the same angle ~8-18x faster. The final rotation is still applied at full resolution by the caller.
    """
    import cv2
    import numpy as np
    from dedocutils.utils import rotate_image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    scale = min(1.0, _SKEW_MIN_SIDE / max(thresh.shape[:2]))  # floor: only downscale, never upscale
    if scale < 1.0:
        thresh = cv2.resize(thresh, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    # coarse GUESS on a smaller thumbnail, then REFINE at full (_SKEW_MIN_SIDE) resolution. The projection-profile score
    # peaks at the same angle at low res (within ~1 deg), so a coarse sweep on the ~512 px thumbnail -- ~7x cheaper per
    # rotation -- brackets the peak just as well, and the full-res +-4 deg refine then recovers the exact angle. ~2x
    # faster than the full-res coarse; matches the 91-step reference as well as the full-res coarse (exact on realistic
    # skew <=12 deg; equivalent on the adversarial >28 deg set where the projection peak is inherently ambiguous).
    cs = min(1.0, _SKEW_COARSE_SIDE / max(thresh.shape[:2]))
    thumb = cv2.resize(thresh, None, fx=cs, fy=cs, interpolation=cv2.INTER_AREA) if cs < 1.0 else thresh

    def score(th, angle):
        rotated = rotate_image(th, angle)
        histogram = np.sum(rotated, axis=1, dtype=float)
        return np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)

    def best_of(th, candidates):
        return candidates[int(np.argmax([score(th, angle) for angle in candidates]))]

    coarse = best_of(thumb, np.arange(-_SKEW_MAX_ANGLE, _SKEW_MAX_ANGLE + 1, 3))
    lo, hi = max(coarse - 4, -_SKEW_MAX_ANGLE), min(coarse + 4, _SKEW_MAX_ANGLE)
    return float(best_of(thresh, np.arange(lo, hi + 0.001, 1)))


def _deskew(config: dict, doc: dict) -> dict:
    import numpy as np
    from dedocutils.utils import rotate_image

    params = doc["params"]
    angle = doc.get("angle", 0)
    angle = angle if params.document_orientation is None else 0
    is_one_column = (doc.get("columns") == 1) if params.is_one_column_document is None else params.is_one_column_document

    image = doc["image"]
    if angle:  # apply the coarse 90/180/270 orientation first (mirrors SkewCorrector.preprocess)
        image = np.rot90(image, angle // 90)
    best_angle = _detect_skew_angle(image)
    # final rotation at full resolution, done once. Skip the warp entirely when there's no skew (best_angle==0), which
    # is the common case for born-digital renders and cleanly-scanned pages -- saves a full-page warpAffine.
    rotated = image if best_angle == 0 else rotate_image(image, best_angle)
    return {**doc, "image": rotated, "rotated_angle": float(angle + best_angle), "is_one_column": is_one_column}


_TABLE_CLASS = 8  # docling-layout-heron label id for 'table' (used to gate the OpenCV table detector)


def _layout_batch(configs: List[dict], docs: List[dict]) -> List[dict]:
    import os
    from dedoc.utils.image_utils import fill_bbox_on_image

    params = docs[0]["params"]
    # the layout model serves two purposes here: extract attachments (Formula/Picture), and, from the SAME forward,
    # report whether a page has a table (class 8) so the expensive per-page OpenCV table detector can be skipped
    if not (params.with_attachments or params.need_pdf_table_analysis):
        return [{**doc, "attachments": []} for doc in docs]

    extractor = _READER.attachments_extractor
    images = [doc["image"] for doc in docs]
    predictions = list(extractor._predict_batch(images))  # one RT-DETR forward for the whole batch of pages
    attachments_dir = os.path.split(docs[0]["path"])[0]
    param_dict = dict(zip(params._fields, params))

    result = []
    for doc, image, prediction in zip(docs, images, predictions):
        # table-presence gate for the OpenCV table stage; None when table analysis is off (so table is not gated)
        has_table = any(int(lid) == _TABLE_CLASS for lid in prediction["labels"]) if params.need_pdf_table_analysis else None
        attachments = []
        if params.with_attachments:
            attachments = extractor._attachments_from_prediction(image, prediction, attachments_dir, "attachment.png", param_dict)
            for attach in attachments:
                attach.location.page_number = doc["page_number"]
                image = fill_bbox_on_image(image, attach.location.bbox)
        result.append({**doc, "image": image, "attachments": attachments, "layout_has_table": has_table})
    return result


def _layout(config: dict, doc: dict) -> dict:
    return _layout_batch([config], [doc])[0]


def _det_pre(config: dict, doc: dict) -> dict:
    # hybrid only: CPU-heavy PP-OCR detection preprocessing, split off the GPU worker to run on the CPU workers
    prepro, ori = _READER.ocr.preprocess(doc["image"])
    return {**doc, "det_prepro": prepro, "det_ori": ori}


def _ocr_gpu(config: dict, doc: dict) -> dict:
    # hybrid GPU stage: DBNet forward + box post-processing + CRNN recognition -> RAW detections (box, text, conf).
    # The CPU line-grouping and metadata are deferred to the meta stage, so the GPU worker does only the NN work.
    import os
    page_gpu = None  # DEDOC_FUSED_DET hands the on-device page from detection to recognition (skips the duplicate H2D)
    if "ocr_boxes" in doc:  # DEDOC_SPLIT_DETPP: DBNet forward + box post already ran (det_forward -> det_postproc)
        boxes = doc["ocr_boxes"]
    elif _READER.config.get("on_gpu") and os.environ.get("DEDOC_FUSED_DET", "1") != "0":  # DEFAULT: GPU-side det preprocess
        preds, ori, page_gpu = _READER.ocr.infer_gpu_from_image(doc["image"])
        boxes = _READER.ocr.postprocess(preds, ori)
    else:
        preds = _READER.ocr.infer(doc["det_prepro"])
        boxes = _READER.ocr.postprocess(preds, doc["det_ori"])
    # GPU-resident recognition when the TensorRT engine is present (has forward_gpu): keeps crops + CRNN logits on-device
    # and downloads only the argmax indices -> ~1/3 less recognition CPU + latency on the GPU worker. Falls back to the
    # CPU-crop path otherwise. Set DEDOC_FUSED_REC=0 to disable.
    if os.environ.get("DEDOC_FUSED_REC", "1") == "1" and hasattr(_READER.ocr._ensure_ppocr_rec().session, "forward_gpu"):
        detections = _READER.ocr.recognize_boxes_fused(doc["image"], boxes, doc["params"].language, page=page_gpu)
    else:
        detections = _READER.ocr.recognize_detections(doc["image"], boxes, doc["params"].language)
    out = {k: v for k, v in doc.items() if k not in ("det_prepro", "ocr_boxes", "det_ori")}
    out["ocr_detections"] = detections
    # piggyback the table cell OCR on the GPU worker: recognize each stacked-cell image (assembled in the meta stage)
    prepared = doc.get("table_prepared")
    if prepared is not None and prepared["stacks"]:
        language = doc["params"].language
        out["table_ocr_results"] = [_hybrid_stack_ocr(stacked, language) for stacked, _ in prepared["stacks"]]
    return out


# --- optional finer split of ocr_gpu (DEDOC_SPLIT_OCR): det_gpu(GPU forward) -> ocr_crop(CPU warpPerspective) ->
# rec_gpu(GPU forward). Moves the ~59 ms/page of box-post + crop CPU work off the GPU worker onto the CPU workers,
# at the cost of shipping the ~5 MB crop list to the rec stage. Whether it wins depends on the CPU/GPU balance.
def _det_gpu(config: dict, doc: dict) -> dict:
    preds = _READER.ocr.infer(doc["det_prepro"])
    boxes = _READER.ocr.postprocess(preds, doc["det_ori"])
    out = {k: v for k, v in doc.items() if k not in ("det_prepro", "det_ori")}
    out["ocr_boxes"] = boxes
    return out


def _ocr_crop(config: dict, doc: dict) -> dict:
    pairs = _READER.ocr.crops_from_boxes(doc["image"], doc["ocr_boxes"])
    out = {k: v for k, v in doc.items() if k != "ocr_boxes"}
    out["ocr_crops"] = pairs
    return out


def _rec_gpu(config: dict, doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "ocr_crops"}
    out["ocr_detections"] = _READER.ocr.recognize_crops(doc["ocr_crops"], doc["params"].language)
    prepared = doc.get("table_prepared")
    if prepared is not None and prepared["stacks"]:
        language = doc["params"].language
        out["table_ocr_results"] = [_hybrid_stack_ocr(stacked, language) for stacked, _ in prepared["stacks"]]
    return out


# --- DEDOC_SPLIT_DETPP: offload the DBNet box POST-processing (pure CPU: findContours/unclip, ~28 ms/page) from the
# GPU worker to the CPU pool, while recognition stays fused on the GPU worker. det_forward(GPU: DBNet fwd) ->
# det_postproc(CPU: DBPostProcess) -> ocr_gpu(GPU: fused recognizer). The DBNet heatmap (~2.7 MB) hops GPU->CPU by
# shared-memory reference; the box post is standalone (no detector model load on the CPU workers).
def _det_forward(config: dict, doc: dict) -> dict:
    preds = _READER.ocr.infer(doc["det_prepro"])
    out = {k: v for k, v in doc.items() if k != "det_prepro"}
    out["ocr_preds"] = preds
    return out


def _det_postproc(config: dict, doc: dict) -> dict:
    boxes = _READER.ocr.postprocess_cpu(doc["ocr_preds"], doc["det_ori"])
    out = {k: v for k, v in doc.items() if k not in ("ocr_preds", "det_ori")}
    out["ocr_boxes"] = boxes
    return out


def _ocr(config: dict, doc: dict) -> dict:
    if "ocr_detections" in doc:  # hybrid: GPU stage returned raw detections; group into lines + metadata here (CPU workers)
        page = _READER.ocr.page_from_detections(doc["ocr_detections"], doc["image"], doc["page_number"])
    else:  # tesseract / easyocr: detect + recognize here
        params = doc["params"]
        page = _READER.ocr.split_image2lines(image=doc["image"], language=params.language,
                                             is_one_column_document=doc.get("is_one_column", True), page_num=doc["page_number"])
    out = {k: v for k, v in doc.items() if k not in ("det_prepro", "ocr_detections", "table_prepared", "table_ocr_results")}
    # assemble tables deferred from the table stage: assign the GPU cell-OCR results onto the tree, rebuild ScanTables
    prepared = doc.get("table_prepared")
    if prepared is not None:
        out["tables"] = _READER.table_recognizer.assemble_tables_from_ocr(doc["image"], prepared, doc.get("table_ocr_results", []))
    if page is None:
        out.update(lines=[], page_attachments=[])
        return out
    lines = _READER.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page)
    out.update(lines=lines, page_attachments=page.attachments)
    return out


class _RecWord:
    __slots__ = ("bbox", "text", "confidence")

    def __init__(self, bbox, text, confidence):
        self.bbox, self.text, self.confidence = bbox, text, confidence


class _RecLine:
    __slots__ = ("bbox", "words")

    def __init__(self, bbox, words):
        self.bbox, self.words = bbox, words


class _RecPage:
    """Minimal duck-typed OcrPage (``.lines`` -> ``.bbox`` + ``.words`` -> ``.bbox/.text/.confidence``) so the hybrid
    recognizer can feed OCRCellExtractor.assign_from_ocr in place of the Tesseract OcrPage. One detection == one line."""
    __slots__ = ("lines",)

    def __init__(self, lines):
        self.lines = lines


def _hybrid_stack_ocr(stacked_gray, language: str) -> _RecPage:
    """GPU: run the hybrid detector+recognizer on one stacked-cell image and adapt the raw ``(box, text, conf)``
    detections into a duck-typed OcrPage. 2.2x faster and higher word-F1 than Tesseract on table cells (see
    TENSORRT_INT8.md). Runs on the GPU worker, piggybacked on the ocr_gpu stage -- no extra CPU<->GPU round-trip."""
    import cv2
    import numpy as np
    from dedocutils.data_structures import BBox
    if stacked_gray is None or stacked_gray.shape[0] < 2 or stacked_gray.shape[1] < 2:
        return _RecPage([])
    bgr = cv2.cvtColor(stacked_gray, cv2.COLOR_GRAY2BGR) if stacked_gray.ndim == 2 else stacked_gray
    try:
        boxes = _READER.ocr.postprocess(_READER.ocr.infer(_READER.ocr.preprocess(bgr)[0]), (bgr.shape[0], bgr.shape[1]))
        # NB: keep the CPU-warpPerspective recognizer here, NOT recognize_boxes_fused. Table stacks are narrow vertical
        # cell concatenations -> almost every box is TINY and TALL (single chars, w~26). Even after matching the GPU
        # tall crop to warpPerspective (see _gpu_native_crop's j/w convention), the fused vs CPU-warp text overlaps only
        # ~40% on real stacks -- recognition of these tiny fragments is unstable, and there is no table-cell ground
        # truth to prove the fused path is neutral. The table-cell OCR was validated against this CPU path.
        dets = _READER.ocr.recognize_detections(bgr, boxes, language)
    except Exception:  # a degenerate stack must never kill the page's tables -> those cells just get no text
        return _RecPage([])
    lines = []
    for box, text, conf in dets:
        if not text:
            continue
        xs, ys = box[:, 0], box[:, 1]
        left, top = int(xs.min()), int(ys.min())
        w, h = max(int(xs.max() - xs.min()), 1), max(int(ys.max() - ys.min()), 1)
        # separate bbox objects: assign_from_ocr mutates the word bbox in place
        lines.append(_RecLine(bbox=BBox(x_top_left=left, y_top_left=top, width=w, height=h),
                              words=[_RecWord(bbox=BBox(x_top_left=left, y_top_left=top, width=w, height=h), text=text, confidence=float(conf) * 100.0)]))
    return _RecPage(lines)


def _table_line_crossings(image, long_side: int = 700) -> int:
    """Cheap table-presence signal (~7 ms/page) using the OpenCV table detector's OWN line-detection parameters
    (fixed 225 threshold to keep faint rules; short horizontal/vertical morphology kernels img//55 & img//100 floored
    at the detector's min cell size), then count grid crossings of the horizontal x vertical rules. Reproducing the
    detector's line detection is what preserves recall: 100% on 503 diverse tables (gen_tables 1/2/3 + real_mixed
    table/hard_table/image_table; the sparsest real table still has 3 crossings) at ~1/50th the detector's cost. Text
    has horizontal runs but no crossing vertical rules, so a page below the threshold has no bordered table the
    detector could find. (A plain Otsu + long-kernel version missed 12% of real tables -- do not simplify further.)"""
    import cv2
    import numpy as np
    from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    scale = long_side / max(gray.shape)
    g = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    img_bin = 255 - cv2.threshold(g, 225, 255, cv2.THRESH_BINARY)[1]
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(g.shape[1] // 55, TableTree.min_w_cell), 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(g.shape[0] // 100, TableTree.min_h_cell)))
    h = cv2.dilate(cv2.erode(img_bin, hk, iterations=2), hk, iterations=2)
    v = cv2.dilate(cv2.erode(img_bin, vk, iterations=2), vk, iterations=2)
    cross = cv2.bitwise_and(cv2.dilate(h, np.ones((5, 5), np.uint8)), cv2.dilate(v, np.ones((5, 5), np.uint8)))
    return cv2.connectedComponents(cross)[0] - 1


def _table(config: dict, doc: dict) -> dict:
    import os
    params = doc["params"]
    if not params.need_pdf_table_analysis:
        return {**doc, "tables": []}
    # layout (GPU) saw no table here -> skip the costly OpenCV contour detection (set DEDOC_TABLE_GATE=0 to disable)
    if doc.get("layout_has_table") is False and os.environ.get("DEDOC_TABLE_GATE", "1") != "0":
        return {**doc, "tables": []}
    # cheap line-crossing gate (detector's own line params -> matches its recall): skip the ~360 ms detector on pages
    # with too few grid crossings for a bordered table. 100% recall on 503 diverse tables (sparsest has 3), so the
    # default threshold 2 keeps a safety margin while skipping ~54% of table-free pages. Set 0 to disable.
    min_cross = int(os.environ.get("DEDOC_TABLE_MIN_CROSS", _READER.config.get("table_line_gate_min_cross", 2)))
    if min_cross > 0 and _table_line_crossings(doc["image"]) < min_cross:
        return {**doc, "tables": []}
    if _READER.config.get("ocr_engine") == "hybrid" and os.environ.get("DEDOC_TABLE_CELL_OCR", "hybrid") == "hybrid":
        # hybrid: detect + filter + mask cells here (CPU); the cell OCR is deferred to the GPU worker (ocr_gpu stage)
        # and the tables are assembled in the ocr metadata stage -- see _ocr_gpu/_ocr. No extra CPU<->GPU round-trip.
        cleaned_image, prepared = _READER.table_recognizer.detect_tables_prepared(
            image=doc["image"], page_number=doc["page_number"], language=params.language, table_type=params.table_type)
        if prepared is None:
            return {**doc, "image": cleaned_image, "tables": []}
        return {**doc, "image": cleaned_image, "table_prepared": prepared}
    clean_image, tables = _READER.table_recognizer.recognize_tables_from_image(
        image=doc["image"], page_number=doc["page_number"], language=params.language, table_type=params.table_type)
    # forward the table-masked image so a downstream OCR does not re-read table cells as body text
    return {**doc, "image": clean_image, "tables": tables}


def setup(config_overrides: Any = None) -> Dict[str, Handler]:
    """Toolkit builder run in each worker process (and in the parent for self-forking tasks).
    ``config_overrides`` lets the GPU worker be built with ``on_gpu=True`` while CPU workers stay on CPU."""
    init_reader(config_overrides)
    return {
        "render": Handler(_render),
        "binarize": Handler(_binarize),
        "orient_pre": Handler(_orient_pre),
        "orient_predict": Handler(_orient_predict, batch_process=_orient_predict_batch),
        "deskew": Handler(_deskew),
        "layout": Handler(_layout, batch_process=_layout_batch),
        "det_pre": Handler(_det_pre),
        "ocr_gpu": Handler(_ocr_gpu),  # per-page: cross-page rec batching adds padding+latency without a compute win
        "det_gpu": Handler(_det_gpu),
        "ocr_crop": Handler(_ocr_crop),
        "rec_gpu": Handler(_rec_gpu),
        "det_forward": Handler(_det_forward),
        "det_postproc": Handler(_det_postproc),
        "ocr": Handler(_ocr),
        "table": Handler(_table),
    }


# spec templates (blockers are filled by build_specs from the config)
_SPEC_DEFS = {
    "render": dict(process=_render, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # pypdfium2 render in the cpu_process pool (PDFium is not thread-safe -> isolated worker processes, not the parent thread pool)
    "binarize": dict(process=_binarize, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
    "orient_pre": dict(process=_orient_pre, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # orient resize/pad on CPU workers
    "orient_predict": dict(process=_orient_predict, resource=Resource.GPU, batch_process=_orient_predict_batch, batch_size=8),
    "deskew": dict(process=_deskew, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
    "layout": dict(process=_layout, resource=Resource.GPU, batch_process=_layout_batch, batch_size=4),
    "det_pre": dict(process=_det_pre, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # hybrid det preprocessing on CPU workers
    "ocr_gpu": dict(process=_ocr_gpu, resource=Resource.GPU),  # hybrid detector+recognizer NN forwards on the GPU worker
    "det_gpu": dict(process=_det_gpu, resource=Resource.GPU),  # DEDOC_SPLIT_OCR: DBNet forward + box post on the GPU worker
    "ocr_crop": dict(process=_ocr_crop, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # warpPerspective crops on CPU workers
    "rec_gpu": dict(process=_rec_gpu, resource=Resource.GPU),  # CRNN/TRT recognizer forward on the GPU worker
    "det_forward": dict(process=_det_forward, resource=Resource.GPU),  # DEDOC_SPLIT_DETPP: DBNet forward only on the GPU worker
    "det_postproc": dict(process=_det_postproc, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # DBNet box post on CPU workers
    "ocr": dict(process=_ocr, resource=Resource.CPU, exec_mode=ExecMode.PROCESS),
    "table": dict(process=_table, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
}


def build_specs(params: Any, ocr_engine: str = "tesseract", on_gpu: bool = False) -> List[TaskSpec]:
    """
    Build the per-page task graph from the request config (ARCHITECTURE.md §9): a stage is present only if
    its parameter enables it, and blockers are the default preprocessing chain restricted to present stages
    (so a missing stage is transparently skipped). This is data, not a hardcoded structure.
    """
    import os
    present = ["render", "deskew", "ocr"]  # render (page image), deskew (rotation/deskew) and ocr always run
    if params.need_binarization:
        present.append("binarize")
    if params.is_one_column_document is None or params.document_orientation is None:
        present.extend(["orient_pre", "orient_predict"])  # orient_pre (CPU resize/pad) -> orient_predict (GPU forward)
    # layout runs for attachments; when it runs, its table detections also gate the OpenCV table stage for free.
    # We do NOT add layout *solely* for the gate: although it cuts the OpenCV table detector from 42% to ~2% of CPU
    # stage-time, the layout NN is a GPU stage and inserts an extra CPU->GPU->CPU->GPU round-trip in the per-page
    # critical path (deskew->layout->table->...->ocr_gpu), whose serialization latency lost +29 s on the 297-page doc
    # even with the GPU ~80% idle. A cheap CPU-side table-presence heuristic would gate without the GPU hop.
    if params.with_attachments:
        present.append("layout")
    if params.need_pdf_table_analysis:
        present.append("table")

    chain = [name for name in ["render", "binarize", "orient_pre", "orient_predict", "deskew", "layout"] if name in present]
    blockers = {name: ([chain[i - 1]] if i > 0 else []) for i, name in enumerate(chain)}
    last = chain[-1] if chain else None
    # table hangs off the preprocessing chain and masks its cells; ocr then reads the table-cleaned image
    # (matches the reference reader's table->clean_image->ocr order). Set ocr's blocker to `last` for the
    # faster sibling variant of ARCHITECTURE.md §9 (at the cost of table text leaking into OCR body lines).
    if "table" in present:
        blockers["table"] = [last] if last else []
    ocr_blocker = "table" if "table" in present else last
    if "ocr" in present:
        blockers["ocr"] = [ocr_blocker] if ocr_blocker else []

    # hybrid: split OCR into det_pre (CPU: detection preprocessing) -> ocr_gpu (GPU: DBNet forward + box post + CRNN
    # recognition) -> ocr (CPU: line-metadata extraction). The GPU worker does only NN forwards; the CPU-heavy
    # preprocessing and metadata run in parallel on the CPU workers, so the GPU device is not starved by CPU work.
    if ocr_engine == "hybrid" and "ocr" in present:
        # DBNet + box post + crop + recognizer all on the GPU worker. Splitting the CPU parts (box post + crop) into a
        # separate CPU stage (det_gpu -> ocr_crop -> rec_gpu) was measured a net loss at gpu_workers>=2 (the extra
        # CPU<->GPU round-trip + ~5 MB crop-list transport outweigh it, and multiple GPU workers already overlap the
        # in-worker CPU work). Kept behind DEDOC_SPLIT_OCR for re-measurement as the CPU/GPU balance shifts.
        if os.environ.get("DEDOC_SPLIT_OCR") == "1":
            present.extend(["det_pre", "det_gpu", "ocr_crop", "rec_gpu"])
            blockers["det_pre"] = blockers["ocr"]
            blockers["det_gpu"] = ["det_pre"]
            blockers["ocr_crop"] = ["det_gpu"]
            blockers["rec_gpu"] = ["ocr_crop"]
            blockers["ocr"] = ["rec_gpu"]
        elif os.environ.get("DEDOC_SPLIT_DETPP") == "1":
            # DBNet box post-processing (pure CPU) moved off the GPU worker to the CPU pool; recognition stays fused.
            present.extend(["det_pre", "det_forward", "det_postproc", "ocr_gpu"])
            blockers["det_pre"] = blockers["ocr"]
            blockers["det_forward"] = ["det_pre"]
            blockers["det_postproc"] = ["det_forward"]
            blockers["ocr_gpu"] = ["det_postproc"]
            blockers["ocr"] = ["ocr_gpu"]
        elif on_gpu and os.environ.get("DEDOC_FUSED_DET", "1") != "0":
            # DEFAULT on GPU: detection preprocessing runs on the GPU worker from the page (GPU resize + TRT/onnx forward
            # via infer_gpu_from_image) -> no det_pre CPU stage, no det_prepro transport, page reused by recognition.
            # DEDOC_FUSED_DET=0 falls back to the CPU det_pre stage (also the path off-GPU).
            present.append("ocr_gpu")
            blockers["ocr_gpu"] = blockers["ocr"]
            blockers["ocr"] = ["ocr_gpu"]
        else:
            present.extend(["det_pre", "ocr_gpu"])
            blockers["det_pre"] = blockers["ocr"]
            blockers["ocr_gpu"] = ["det_pre"]
            blockers["ocr"] = ["ocr_gpu"]

    specs = []
    for name in present:
        spec_def = dict(_SPEC_DEFS[name])
        if not on_gpu and spec_def.get("resource") == Resource.GPU:
            # Without a GPU there is no device to share, so a "GPU" stage is just ordinary CPU work. Leaving it routed
            # to the gpu pool pins every forward to that single worker, which runs them serially and starves the CPU
            # pool: measured on Catalana 24p, CPU-only, orient_predict alone -> 8 workers were *slower* than 1
            # (54.1s vs 48.9s) with only ~25% of the cores busy. Route these to the CPU workers so they parallelize
            # per page like every other CPU stage; batching only pays off on a device (one forward per batch), so it
            # is dropped here in favour of per-page spread.
            spec_def["resource"] = Resource.CPU
            spec_def["exec_mode"] = ExecMode.THREAD
            spec_def.pop("batch_process", None)
            spec_def["batch_size"] = 1
        if name == "ocr" and ocr_engine == "hybrid":  # ocr is now the CPU metadata stage -> run it on the CPU workers
            spec_def["exec_mode"] = ExecMode.THREAD
        specs.append(TaskSpec(name=name, blockers=blockers.get(name, []), **spec_def))
    return specs
