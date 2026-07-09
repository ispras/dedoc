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


def init_reader(config_overrides: Optional[dict] = None) -> Any:
    global _READER
    if _READER is None:
        from dedoc.config import get_config
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        _READER = PdfImageReader(config={**get_config(), **(config_overrides or {})})
    return _READER


# ---------------------------------------------------------------- stage handlers

def _render(config: dict, doc: dict) -> dict:
    """Render this page's image on demand (lazy render): a PDF page -> bitmap, or load an image file.
    Mirrors PdfBaseReader._get_images / _split_pdf2image for a single page (default DPI, BGR->RGB)."""
    import cv2
    import numpy as np
    from dedoc.extensions import recognized_mimes
    from dedoc.utils.utils import get_file_mime_type

    path, page_number = doc["path"], doc["page_number"]
    if get_file_mime_type(path) in recognized_mimes.pdf_like_format or path.lower().endswith(".pdf"):
        from pdf2image import convert_from_path
        rendered = convert_from_path(path, first_page=page_number + 1, last_page=page_number + 1)
        image = cv2.cvtColor(np.array(rendered[0]), cv2.COLOR_BGR2RGB)
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


_SKEW_MIN_SIDE = 1000  # detect the fine skew on an image downscaled to this long side; never upscale a low-res page
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

    def score(angle):
        rotated = rotate_image(thresh, angle)
        histogram = np.sum(rotated, axis=1, dtype=float)
        return np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)

    def best_of(candidates):
        scores = [score(angle) for angle in candidates]
        return candidates[int(np.argmax(scores))]

    # coarse-to-fine: a full 1-deg sweep over +-45 is 91 rotations/page. Instead bracket the projection-profile peak
    # with a coarse 3-deg sweep (31 rotations), then refine at 1 deg around it (7 more) = 38 vs 91, ~2.4x fewer. The
    # score is smooth over 3 deg so the coarse grid always brackets the peak -> identical angle (validated against the
    # 91-step sweep on injected skews of 0-12 deg: exact match).
    coarse = best_of(np.arange(-_SKEW_MAX_ANGLE, _SKEW_MAX_ANGLE + 1, 3))
    lo, hi = max(coarse - 3, -_SKEW_MAX_ANGLE), min(coarse + 3, _SKEW_MAX_ANGLE)
    return float(best_of(np.arange(lo, hi + 0.001, 1)))


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
    rotated = rotate_image(image, best_angle)  # final rotation at full resolution, done once (output unchanged)
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
    preds = _READER.ocr.infer(doc["det_prepro"])
    boxes = _READER.ocr.postprocess(preds, doc["det_ori"])
    detections = _READER.ocr.recognize_detections(doc["image"], boxes, doc["params"].language)
    out = {k: v for k, v in doc.items() if k != "det_prepro"}
    out["ocr_detections"] = detections
    return out


def _ocr(config: dict, doc: dict) -> dict:
    if "ocr_detections" in doc:  # hybrid: GPU stage returned raw detections; group into lines + metadata here (CPU workers)
        page = _READER.ocr.page_from_detections(doc["ocr_detections"], doc["image"], doc["page_number"])
    else:  # tesseract / easyocr: detect + recognize here
        params = doc["params"]
        page = _READER.ocr.split_image2lines(image=doc["image"], language=params.language,
                                             is_one_column_document=doc.get("is_one_column", True), page_num=doc["page_number"])
    if page is None:
        return {**doc, "lines": [], "page_attachments": []}
    lines = _READER.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page)
    out = {k: v for k, v in doc.items() if k not in ("det_prepro", "ocr_detections")}
    out.update(lines=lines, page_attachments=page.attachments)
    return out


def _table(config: dict, doc: dict) -> dict:
    import os
    params = doc["params"]
    if not params.need_pdf_table_analysis:
        return {**doc, "tables": []}
    # layout (GPU) saw no table here -> skip the costly OpenCV contour detection (set DEDOC_TABLE_GATE=0 to disable)
    if doc.get("layout_has_table") is False and os.environ.get("DEDOC_TABLE_GATE", "1") != "0":
        return {**doc, "tables": []}
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
        "ocr": Handler(_ocr),
        "table": Handler(_table),
    }


# spec templates (blockers are filled by build_specs from the config)
_SPEC_DEFS = {
    "render": dict(process=_render, resource=Resource.CPU, exec_mode=ExecMode.PROCESS),  # Poppler self-forks pdftoppm
    "binarize": dict(process=_binarize, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
    "orient_pre": dict(process=_orient_pre, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # orient resize/pad on CPU workers
    "orient_predict": dict(process=_orient_predict, resource=Resource.GPU, batch_process=_orient_predict_batch, batch_size=8),
    "deskew": dict(process=_deskew, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
    "layout": dict(process=_layout, resource=Resource.GPU, batch_process=_layout_batch, batch_size=4),
    "det_pre": dict(process=_det_pre, resource=Resource.CPU, exec_mode=ExecMode.THREAD),  # hybrid det preprocessing on CPU workers
    "ocr_gpu": dict(process=_ocr_gpu, resource=Resource.GPU),  # hybrid detector+recognizer NN forwards on the GPU worker
    "ocr": dict(process=_ocr, resource=Resource.CPU, exec_mode=ExecMode.PROCESS),
    "table": dict(process=_table, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
}


def build_specs(params: Any, ocr_engine: str = "tesseract") -> List[TaskSpec]:
    """
    Build the per-page task graph from the request config (ARCHITECTURE.md §9): a stage is present only if
    its parameter enables it, and blockers are the default preprocessing chain restricted to present stages
    (so a missing stage is transparently skipped). This is data, not a hardcoded structure.
    """
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
        # separate CPU stage (det_gpu -> crop -> rec_gpu) was measured: it helps with a single GPU worker (-11%) but is
        # a net loss once gpu_workers>=2 (the extra CPU->GPU->CPU->GPU round-trip + crop-list transport outweigh it, and
        # multiple GPU workers already parallelize the in-worker CPU work for free). See TENSORRT_INT8.md.
        present.extend(["det_pre", "ocr_gpu"])
        blockers["det_pre"] = blockers["ocr"]
        blockers["ocr_gpu"] = ["det_pre"]
        blockers["ocr"] = ["ocr_gpu"]

    specs = []
    for name in present:
        spec_def = dict(_SPEC_DEFS[name])
        if name == "ocr" and ocr_engine == "hybrid":  # ocr is now the CPU metadata stage -> run it on the CPU workers
            spec_def["exec_mode"] = ExecMode.THREAD
        specs.append(TaskSpec(name=name, blockers=blockers.get(name, []), **spec_def))
    return specs
