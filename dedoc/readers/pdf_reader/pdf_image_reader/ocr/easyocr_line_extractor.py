"""
EasyOCR-based line extractor - a drop-in alternative to :class:`OCRLineExtractor` (Tesseract).

Selectable via ``config["ocr_engine"] = "easyocr"`` so both OCR engines live in the project side by side and
can be swapped without touching the rest of the pipeline. It returns the SAME :class:`PageWithBBox` structure
(lines of words, each word carrying a bbox + per-word confidence/bbox annotations) that the Tesseract path
returns, so everything downstream (``LineMetadataExtractor``, structure extraction) is unchanged.

EasyOCR is torch-based (fits the existing CUDA torch), Apache-2.0, and has strong Cyrillic support. Unlike
Tesseract it does detection + recognition in one shot and returns a flat list of text regions; we regroup those
regions into rows (dedoc "lines") and words to match Tesseract's line/word contract.
"""
import logging
from typing import List, Optional, Tuple

import numpy as np
from dedocutils.data_structures import BBox

from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.data_classes.word_with_bbox import WordWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_line import OcrLine
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_word import OcrWord

# dedoc/Tesseract language codes -> EasyOCR language codes
_LANG_MAP = {"eng": "en", "rus": "ru", "fra": "fr", "deu": "de", "spa": "es", "ita": "it", "por": "pt", "nld": "nl",
             "en": "en", "ru": "ru", "fr": "fr", "de": "de", "es": "es", "it": "it", "pt": "pt", "nl": "nl"}


def _map_languages(language: str) -> List[str]:
    """Map a Tesseract-style ``+``-joined language string (e.g. ``"rus+eng"``) to EasyOCR codes (``["ru", "en"]``)."""
    langs: List[str] = []
    for token in (language or "eng").split("+"):
        code = _LANG_MAP.get(token.strip().lower())
        if code and code not in langs:
            langs.append(code)
    return langs or ["en"]


class EasyOCRLineExtractor:

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self._reader = None
        self._reader_langs: Optional[Tuple[str, ...]] = None

    def _get_reader(self, language: str):
        """Lazily build (and cache per language set) the EasyOCR reader; GPU follows ``config["on_gpu"]``."""
        import easyocr

        key = tuple(_map_languages(language))
        if self._reader is None or self._reader_langs != key:
            gpu = bool(self.config.get("on_gpu", False))
            # DBNet18 detector: ~2.5x faster than the default CRAFT at full resolution (lighter box post-processing),
            # and faster than Tesseract per page. Needs the compiled deform-conv CUDA op (easyocr/DBNet/assets/ops/dcn).
            detector = self.config.get("easyocr_detector", "dbnet18")
            self.logger.info(f"Building EasyOCR reader langs={list(key)} gpu={gpu} detector={detector}")
            self._reader = easyocr.Reader(list(key), gpu=gpu, detect_network=detector)
            self._reader_langs = key
        return self._reader

    def split_image2lines(self, image: np.ndarray, page_num: int, language: str = "rus+eng", is_one_column_document: bool = True) -> PageWithBBox:
        reader = self._get_reader(language)
        # keep full detection resolution (2560) so small text is not degraded - the DBNet detector already makes this
        # fast; lowering canvas_size trades OCR quality for speed and is left as an opt-in knob. batch_size batches
        # recognition crops through the CRNN.
        canvas_size = int(self.config.get("easyocr_canvas_size", 2560))
        batch_size = int(self.config.get("easyocr_batch_size", 16))
        # EasyOCR returns [ [4-point box], text, confidence(0..1) ] per detected text region
        detections = reader.readtext(image, detail=1, paragraph=False, canvas_size=canvas_size, batch_size=batch_size)

        ocr_conf_threshold = self.config.get("ocr_conf_threshold", -1)
        extract_line_bbox = self.config.get("labeling_mode", False)
        height, width = image.shape[:2]

        ocr_lines = self._detections_to_lines(detections, ocr_conf_threshold)

        lines_with_bbox = []
        for line_num, line in enumerate(ocr_lines):
            words = [WordWithBBox(text=word.text, bbox=word.bbox) for word in line.words]
            annotations = line.get_annotations(width, height, extract_line_bbox)  # reuse Tesseract path's annotation build
            lines_with_bbox.append(TextWithBBox(words=words, page_num=page_num, bbox=line.bbox, line_num=line_num, annotations=annotations))

        # same aspect-ratio sanity filter as OCRLineExtractor._filtered_bboxes
        filtered = [line for line in lines_with_bbox if 0.01 < line.bbox.height / (line.bbox.width + 1e-6) < 24]
        return PageWithBBox(page_num=page_num, bboxes=filtered, image=image)

    @staticmethod
    def _detections_to_lines(detections: list, ocr_conf_threshold: float) -> List[OcrLine]:
        # 1) normalize each detection to an axis-aligned BBox; drop empties and (scaling conf 0..1 -> 0..100) low-conf
        items = []
        for box, text, conf in detections:
            text = (text or "").strip()
            if not text or conf * 100 < ocr_conf_threshold:
                continue
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            x0, y0 = int(round(min(xs))), int(round(min(ys)))
            bbox = BBox(x0, y0, int(round(max(xs) - min(xs))), int(round(max(ys) - min(ys))))
            items.append((bbox, text, float(conf)))

        # 2) group detections into rows (a dedoc "line") by vertical proximity - EasyOCR often already returns a whole
        #    line as one box, but split fragments are rejoined here so reading order matches Tesseract's line grouping
        items.sort(key=lambda it: it[0].y_top_left + it[0].height / 2)
        rows: List[list] = []
        for bbox, text, conf in items:
            y_center = bbox.y_top_left + bbox.height / 2
            if rows:
                ref = rows[-1]
                ref_y = sum(b.y_top_left + b.height / 2 for b, _, _ in ref) / len(ref)
                ref_h = sum(b.height for b, _, _ in ref) / len(ref)
                if abs(y_center - ref_y) <= max(ref_h, bbox.height) * 0.5:
                    ref.append((bbox, text, conf))
                    continue
            rows.append([(bbox, text, conf)])

        # 3) build OcrLine/OcrWord (reused so OcrLine.get_annotations emits the same Confidence/BBox annotations)
        ocr_lines = []
        for line_num, row in enumerate(rows):
            row.sort(key=lambda it: it[0].x_top_left)  # left-to-right reading order
            words = [OcrWord(text=text, bbox=bbox, confidence=conf * 100, order=i) for i, (bbox, text, conf) in enumerate(row)]
            ocr_lines.append(OcrLine(order=line_num, bbox=_union_bbox([bbox for bbox, _, _ in row]), words=words))
        return ocr_lines


def _union_bbox(bboxes: List[BBox]) -> BBox:
    x0 = min(b.x_top_left for b in bboxes)
    y0 = min(b.y_top_left for b in bboxes)
    x1 = max(b.x_bottom_right for b in bboxes)
    y1 = max(b.y_bottom_right for b in bboxes)
    return BBox(x0, y0, x1 - x0, y1 - y0)
