import logging
import math
from copy import deepcopy
from itertools import chain
from typing import List, Optional

import numpy as np

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier import get_classifiers
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_result import TxtLayerResult
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.utils.parameter_utils import get_bool_parameter, get_param_page_slice, get_param_pdf_with_txt_layer, get_param_with_attachments
from dedoc.utils.pdf_utils import get_pdf_page_count


class TxtLayerDetector:

    def __init__(self, pdf_reader: PdfTabbyReader, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

        self.classifiers = get_classifiers(config=config)
        self.pdf_reader = pdf_reader

    def detect_txtlayer(self, path: str, parameters: dict) -> List[TxtLayerResult]:
        """
        Detect if the PDF document has a textual layer.

        :param path: path to the PDF file
        :param parameters: parameters for the txtlayer classifier
        :return: information about a textual layer in the PDF document
        """
        classifier_name = str(parameters.get("textual_layer_classifier", "ml")).lower()
        txtlayer_classifier = self.classifiers.get(classifier_name)
        if txtlayer_classifier is None:
            raise ValueError(f"Unknown textual layer classifier `{classifier_name}`")

        start, end = get_param_page_slice(parameters)
        start = 1 if start is None else start + 1

        classify_each_page = get_bool_parameter(parameters, "each_page_textual_layer_detection", False)
        detect_function = self.__classify_each_page if classify_each_page else self.__classify_all_pages
        try:
            return detect_function(path, parameters, txtlayer_classifier, start, end)
        except Exception as e:
            self.logger.debug(f"Error occurred white detecting PDF textual layer ({e})")
            return [TxtLayerResult(correct=False, start=start, end=end)]

    def __classify_all_pages(
            self, path: str, parameters: dict, txtlayer_classifier: AbstractTxtlayerClassifier, start: int, end: Optional[int]
    ) -> List[TxtLayerResult]:
        """
        Check only first 8 pages of the document, use classification results for the entire document.
        Separately handle the first page (it's common that only first page doesn't have a textual layer).
        """
        parameters_copy = deepcopy(parameters)
        # When the whole document already fits inside the 8-page detection window, extract it once with the *full*
        # parameters (all pages + tables, matching __parse_document's own read) and hand the result to
        # __parse_document via TxtLayerResult.document -- this avoids launching a second tabby/Java subprocess to
        # re-extract the same pages, ~halving the wall for small text-layer documents (common in prod). Larger
        # documents keep the cheap first-8-pages-only, no-tables detection.
        page_count = get_pdf_page_count(path)
        reusable = page_count is not None and page_count <= 8 and start == 1 and end is None
        # For longer documents the detection window cannot replace the whole read, but its extraction is still not
        # wasted: tabby's raw per-page output is handed to PdfTabbyReader, which then extracts only the pages the
        # detection did not cover. This is free -- the tabby reader ignores need_pdf_table_analysis, so this read
        # already produces a complete extraction of those pages, which used to be thrown away. Restricted to:
        #  * auto_tabby -- under "auto" the document is read by pdf_txtlayer_reader, which cannot consume tabby's pages;
        #  * runs without attachments -- extracted image files live in this read's temporary directory, which is gone
        #    by the time the second read would reference them.
        pages_reusable = (
            not reusable
            and start == 1  # noqa W503
            and get_param_pdf_with_txt_layer(parameters) == "auto_tabby"  # noqa W503
            and not get_param_with_attachments(parameters)  # noqa W503
        )
        detected_pages = [] if pages_reusable else None
        if reusable:
            parameters_copy["pages"] = "1:"  # exactly __parse_document's slice for a whole-document request; tables kept on
        else:
            parameters_copy["pages"] = "1:8"  # two batches for pdf_txtlayer_reader
            parameters_copy["need_pdf_table_analysis"] = "false"
            if pages_reusable:
                parameters_copy["__tabby_raw_pages_out"] = detected_pages

        document = self.pdf_reader.read(path, parameters=parameters_copy)
        reuse_document = document if reusable else None
        detected_last_page = len(detected_pages) if detected_pages else 0
        is_correct = txtlayer_classifier.predict([document.lines])[0]
        if not is_correct:
            return [TxtLayerResult(correct=False, start=start, end=end)]

        if start > 1:  # no need to classify correctness of the first page
            return [TxtLayerResult(correct=True, start=start, end=end, document=reuse_document)]

        first_page_lines = [line for line in document.lines if line.metadata.page_id == 0]
        first_page_correct = txtlayer_classifier.predict([first_page_lines])[0]
        if first_page_correct:
            return [
                TxtLayerResult(
                    correct=True,
                    start=start,
                    end=end,
                    document=reuse_document,
                    detected_pages=detected_pages,
                    detected_last_page=detected_last_page
                )
            ]
        else:
            # the leading pages are not read as one chunk here, so the detection extraction cannot be reused as-is
            return [TxtLayerResult(correct=False, start=start, end=start), TxtLayerResult(correct=True, start=start + 1, end=end)]

    def __classify_each_page(
            self, path: str, parameters: dict, txtlayer_classifier: AbstractTxtlayerClassifier, start: int, end: Optional[int]
    ) -> List[TxtLayerResult]:
        """
        Classify each page of the document correct/not correct textual layer.
        """
        document = self.pdf_reader.read(path, parameters=parameters)
        if not document.lines:
            return [TxtLayerResult(correct=False, start=start, end=end)]

        # Prepare lines for prediction - list of pages
        lines = sorted(document.lines, key=lambda l: (l.metadata.page_id, l.metadata.line_id))
        lines_for_predict = []
        fisrt_page_id = start - 1
        last_page_id = lines[-1].metadata.page_id
        current_line_idx = 0

        for page_id in range(fisrt_page_id, last_page_id + 1):
            current_lines = []
            for line_idx, line in enumerate(lines[current_line_idx:]):
                if line.metadata.page_id != page_id:
                    current_line_idx += line_idx
                    break
                current_lines.append(line)
            lines_for_predict.append(current_lines)

        predictions = txtlayer_classifier.predict(lines_for_predict)
        # e.g. predictions = [0, 0, 1, 1, 0, 1, 0, 0, 1], transitions = [2, 4, 5, 6, 8]
        transitions = list(np.where(predictions[:-1] != predictions[1:])[0] + 1)
        transitions.append(len(predictions))
        result: List[TxtLayerResult] = []

        # Split document into chunks with different value of the textual layer correctness
        is_correct = predictions[0]
        prev_idx = 0
        for transition_idx in transitions:
            chunk_lines = list(chain.from_iterable(lines_for_predict[prev_idx:transition_idx]))
            if is_correct:
                chunk_document = UnstructuredDocument(lines=chunk_lines, tables=document.tables, attachments=document.attachments)
            else:
                chunk_document = None
            chunk_result = TxtLayerResult(start=prev_idx + fisrt_page_id + 1, end=transition_idx + fisrt_page_id, correct=is_correct, document=chunk_document)
            result.append(chunk_result)
            is_correct = not is_correct
            prev_idx = transition_idx

        # Handle last pages without textual layer
        page_count = get_pdf_page_count(path)
        end_numeric_value = min(page_count or math.inf, end or math.inf)
        start_value = prev_idx + fisrt_page_id + 1
        end_value = end or page_count
        if end_value is None or start_value <= end_numeric_value:
            if result and not result[-1].correct:
                result[-1].end = end_value
            else:
                result.append(TxtLayerResult(start=start_value, end=end_value, correct=False))

        return result
