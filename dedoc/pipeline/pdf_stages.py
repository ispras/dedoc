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


def _orient_predict(config: dict, doc: dict) -> dict:
    columns, angle = _READER.column_orientation_classifier.predict(doc["image"])
    return {**doc, "columns": columns, "angle": angle}


def _orient_predict_batch(configs: List[dict], docs: List[dict]) -> List[dict]:
    # single forward pass over the whole batch of page images (task #4)
    results = _READER.column_orientation_classifier.predict_batch([d["image"] for d in docs])
    return [{**doc, "columns": columns, "angle": angle} for doc, (columns, angle) in zip(docs, results)]


def _deskew(config: dict, doc: dict) -> dict:
    params = doc["params"]
    angle = doc.get("angle", 0)
    angle = angle if params.document_orientation is None else 0
    is_one_column = (doc.get("columns") == 1) if params.is_one_column_document is None else params.is_one_column_document
    rotated_image, result_angle = _READER.skew_corrector.preprocess(doc["image"], {"orientation_angle": angle})
    return {**doc, "image": rotated_image, "rotated_angle": result_angle["rotated_angle"], "is_one_column": is_one_column}


def _layout_batch(configs: List[dict], docs: List[dict]) -> List[dict]:
    import os
    from dedoc.utils.image_utils import fill_bbox_on_image

    params = docs[0]["params"]
    if not params.with_attachments:
        return [{**doc, "attachments": []} for doc in docs]

    attachments_dir = os.path.split(docs[0]["path"])[0]
    images = [doc["image"] for doc in docs]
    # one RT-DETR forward for the whole batch of pages
    per_page = _READER.attachments_extractor.extract_batch(images, attachments_dir, dict(zip(params._fields, params)))

    result = []
    for doc, image, attachments in zip(docs, images, per_page):
        for attach in attachments:
            attach.location.page_number = doc["page_number"]
            image = fill_bbox_on_image(image, attach.location.bbox)
        result.append({**doc, "image": image, "attachments": attachments})
    return result


def _layout(config: dict, doc: dict) -> dict:
    return _layout_batch([config], [doc])[0]


def _ocr(config: dict, doc: dict) -> dict:
    params = doc["params"]
    page = _READER.ocr.split_image2lines(image=doc["image"], language=params.language,
                                         is_one_column_document=doc.get("is_one_column", True), page_num=doc["page_number"])
    if page is None:
        return {**doc, "lines": [], "page_attachments": []}
    lines = _READER.metadata_extractor.extract_metadata_and_set_annotations(page_with_lines=page)
    return {**doc, "lines": lines, "page_attachments": page.attachments}


def _table(config: dict, doc: dict) -> dict:
    params = doc["params"]
    if not params.need_pdf_table_analysis:
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
        "orient_predict": Handler(_orient_predict, batch_process=_orient_predict_batch),
        "deskew": Handler(_deskew),
        "layout": Handler(_layout, batch_process=_layout_batch),
        "ocr": Handler(_ocr),
        "table": Handler(_table),
    }


# spec templates (blockers are filled by build_specs from the config)
_SPEC_DEFS = {
    "render": dict(process=_render, resource=Resource.CPU, exec_mode=ExecMode.PROCESS),  # Poppler self-forks pdftoppm
    "binarize": dict(process=_binarize, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
    "orient_predict": dict(process=_orient_predict, resource=Resource.GPU, batch_process=_orient_predict_batch, batch_size=8),
    "deskew": dict(process=_deskew, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
    "layout": dict(process=_layout, resource=Resource.GPU, batch_process=_layout_batch, batch_size=4),
    "ocr": dict(process=_ocr, resource=Resource.CPU, exec_mode=ExecMode.PROCESS),
    "table": dict(process=_table, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
}


def build_specs(params: Any) -> List[TaskSpec]:
    """
    Build the per-page task graph from the request config (ARCHITECTURE.md §9): a stage is present only if
    its parameter enables it, and blockers are the default preprocessing chain restricted to present stages
    (so a missing stage is transparently skipped). This is data, not a hardcoded structure.
    """
    present = ["render", "deskew", "ocr"]  # render (page image), deskew (rotation/deskew) and ocr always run
    if params.need_binarization:
        present.append("binarize")
    if params.is_one_column_document is None or params.document_orientation is None:
        present.append("orient_predict")
    if params.with_attachments:
        present.append("layout")
    if params.need_pdf_table_analysis:
        present.append("table")

    chain = [name for name in ["render", "binarize", "orient_predict", "deskew", "layout"] if name in present]
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

    return [TaskSpec(name=name, blockers=blockers.get(name, []), **dict(_SPEC_DEFS[name])) for name in present]
